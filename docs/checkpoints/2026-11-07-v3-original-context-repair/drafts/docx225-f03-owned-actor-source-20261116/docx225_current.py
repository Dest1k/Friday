"""Inert retained own-native DOCX F03 current225 Source checker. Root-only future calls.
No import IO, authority issuance, upload, converter, Office, fallback or replay."""
from __future__ import annotations
import ast
import contextlib
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import sqlite3
import sys
import importlib
import stat
import subprocess
import time
import types

H = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
STATE = Path('/home/jericho/.local/share/friday-telegram-bot-test')
SLOT = Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
SID = '20261030_093055_43bba39f'
KEY = 'agent:telegram-bot-8812646969:telegram:dm:8812646969'
DEFAULT_LIMIT = 1024**2
EXACT_LIMIT = 24*1024**2
CLOSURE = {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE225-ROOT-SOURCE-INTEGRATION-20261116/ROOT-NATIVE225-CLOSED.json', 'bytes': 14416, 'sha256': '14fb7377ef5d0089a10c4cd0d1f204def146124e54c84b31aa7a5e81acbd53b9'}
ACCEPTANCE = {'path': '/home/jericho/.cache/FRW-ASTRA-DOCX225-ROOT-FRAME-SOURCE-20261116/bound-source-frame225-9ad40f35-r3/ROOT-225-SOURCE-ACCEPTANCE.json', 'bytes': 4310, 'sha256': '3824140268f62cf1b3f7c48d141796709635245bcd55932ee488dd5d77ac37af'}
PREP = {'path': '/home/jericho/.cache/FRW-ASTRA-DOCX-F03-OWNED-ACTOR-ROOT-INPUTS-20261116/operational-source/docx225_prepare.history-r2.py', 'bytes': 10069, 'sha256': 'ef5580d1ed9d90eb6b80bb5893f0b8b587c304eb38861b8e162a1ea3dc13e2fb'}
TRANSPORT = {'path': '/home/jericho/.cache/FRW-ASTRA-DOCX225-ROOT-FRAME-SOURCE-20261116/bound-source-frame225-9ad40f35-r3/native_scope_post225.py', 'bytes': 5878, 'sha256': '73feb894b472734220cd9956a50a878895798ebd90dda9de0bc954a8b4e7840e'}
SOURCE_LEAVES_ACCEPTANCE = {'path': '/home/jericho/.cache/FRW-ASTRA-DOCX-F03-OWNED-ACTOR-ROOT-INPUTS-20261116/ROOT-F03-SOURCE-LEAVES-ACCEPTED.json', 'bytes': 1817, 'sha256': '14ca2c205671131cbde90a2ae46bd622904bf2f3d561894602c735a00b0eaeaa'}
SEMANTIC_EVALUATOR = {'path': '/home/jericho/.cache/FRW-ASTRA-DOCX-F03-OWNED-ACTOR-ROOT-INPUTS-20261116/evaluation/docx_onefact_source.py', 'sha256': '50a67989ebd50235fa4e32fd782ffbc500499256fa456aa5766ef138dcfabc7e', 'bytes': 7056}
SELECTED_SHA = 'cc36c0933bd01cfa5c33a3fb1123fefd0345a2185fbcf7f70f5a3bc2f7c0905b'
COUNTS = {'layers': 225, 'project': 531, 'native': 17894, 'plugins': 52, 'base': 17730}
RECEIPT_SHA = 'c3998841e16c406236d521a987425365a8469a0f752cba9077ddecabfe252195'
INPUT_SHA = '75f5906d74f905be3daef0f5219543228e72c1b2a0e99e1ab5be998ef3cf187c'
SOURCE_COMMIT = '9ad40f35a841e52b78159f7f9397343c8b5495de'
PROJECTION_LIMIT = 'ALL_PROFILE_IN_MEMORY_PENDING_QUEUES_APPROVALS_NOT_EXPOSED'
LOGGING_SITES = ('agent/turn_context.py','gateway/run_turn.py')
LEAF_PINS = {'hermes_cli/friday_user_scope.py': 'abad3f299d1099914455781176ac0a3e09b4d40d4a2afd14b342dcb990087dba', 'hermes_cli/friday_workspace_revision.py': 'a84959c7ddc6fec3a028e5b67b4af64b7ee5d7f462776b9a59150a1891b10dc4', 'tools/file_tools.py': '98c34240d4285bb22d970466043900fa7a0ef8557126e16726e93785d6c0ef9b', 'tools/binary_extensions.py': 'dce64d721d3541194d967f4b1edc9c4ae97e8e30fc64df20d606365ab70132de', 'tools/read_extract.py': '8f3ad405263470eac948a9f14fa6c0af18144697cf5244c6c8c8a4f7d543b339', 'tools/scoped_zip.py': 'fdb74316af13069b30acab144dd2d846a7643e7941acc157cfc6ba0b4ddfc127', 'tools/scoped_word_profiles.py': 'c2e579cd399fbaa95c68f3c167b7c88e1970c5d3f0f0c309fd96f9d442ad101a', 'tools/scoped_word_located.py': '4daa683e0a85a15f349d6a6e9b7940cff9761bbc20a003c6aed8fa9f6b2285db', 'hermes_cli/friday_workspace_docx.py': '289bab471507b7477afc4c95cde7a878199d9e74a1d1c528d80f5d371b985608', 'hermes_cli/friday_product_access.py': 'afd6fe8fd51a170887977286b9ef7a92a7aa76286b817b7a56075069ddab3582', 'agent/web_call_context.py': '83481eaf08254db6dc742419d0615b40c3a1711a8167b0d3c63a67c7d6826042', 'tools/file_tools_write_guards.py': '81df0dd7e0415a3c95870ce0935c132a6535e4be2ca44d3001638a0a1dcfad2c', 'tools/file_tools_paths.py': '50fe4d04a31c3b0377b422ef394d6ccdf1bc1b75ac61bdc6962e0ad802397f69', 'hermes_cli/plugins_state.py': 'a1a509fc2b8dc8e4082837f303d754c9dc62ba450f980b3281af946822923b4d'}
RELEVANT = (*LEAF_PINS,'gateway/ordinary_turn_projection.py',*LOGGING_SITES)
TIMING = dict(operation_seconds=300,reply_window_seconds=180,ack_seconds=10,reserve_seconds=5,outer_seconds=600)
SESSION_FIELDS = ('id','source','user_id','chat_id','chat_type','session_key','profile_name','transport_profile')
MESSAGE_FIELDS = ('id','session_id','role','timestamp','platform_message_id','active','compacted')
PRINCIPAL = dict(id=SID,source='telegram',user_id='8812646969',chat_id='8812646969',chat_type='dm',session_key=KEY,profile_name='telegram-bot-8812646969',transport_profile='default')
DATABASES = {'default':H/'state.db','dest':H/'profiles/dest_telegram/state.db','tester':H/'profiles/telegram-bot-8812646969/state.db'}
# Only these three known profile configs have a separate prospective read bound.
# Bounds are fixed before reading, never inferred from file size or a failed read.
PROFILE_CONFIG_LIMITS = {'default':4*1024**2,'dest':DEFAULT_LIMIT,'tester':4*1024**2}
PROOF_FIELDS = {'schema','status','operator','effect','whole_effect_sha256','created_at','expires_at','created_monotonic','expires_monotonic','boot_id','observed','lock_owners','invocation','Root_decision','privacy_preflight'}
EFFECT_FIELDS = {'schema','run_id','phase','authority','scenario','checker','source_preparation','installation_closure','source_acceptance','resources'}


def need(ok, code):
    if not ok: raise ValueError(code)


def encoded(value):
    return (json.dumps(value,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()


def digest(raw): return hashlib.sha256(raw).hexdigest()
def clone(value): return json.loads(encoded(value))
def sha(value): return type(value) is str and re.fullmatch('[a-f0-9]{64}',value) is not None


def unique(pairs):
    result={}
    for key,value in pairs:
        need(key not in result,'F07_DUPLICATE_JSON_KEY'); result[key]=value
    return result


def parse(raw): return json.loads(raw,object_pairs_hook=unique)


def canonical_path(value):
    text=str(value) if isinstance(value,Path) else value
    need(type(text) is str and text.startswith('/') and not text.startswith('//')
         and all(ord(c)>=32 and not 127<=ord(c)<=159 for c in text)
         and str(Path(text))==text and all(p not in ('','.','..') for p in text.split('/')[1:]),
         'F07_CANONICAL_PATH_REQUIRED')
    text.encode('utf-8'); return Path(text)


def identity(s):
    return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_uid','st_gid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))


def _read_bounded(path,limit,private):
    p=canonical_path(path)
    need(type(limit) is int and 0<limit<=EXACT_LIMIT,'F07_EXACT_READ_BOUND_REQUIRED')
    need(not any(q.is_symlink() for q in (p,*p.parents)),'F07_NO_SYMLINKS_REQUIRED')
    with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
        before=os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1
             and not stat.S_IMODE(before.st_mode)&0o002
             and (not private or stat.S_IMODE(before.st_mode)==0o600),'F07_UNSAFE_INPUT')
        raw=stream.read(limit+1); after=os.fstat(stream.fileno())
    need(len(raw)<=limit and len(raw)==before.st_size and identity(before)==identity(after)==identity(p.stat()),'F07_INPUT_CAS_OR_SIZE_CHANGED')
    return raw


def read(path,*,private=True):
    """Proven path ABI: default1MiB; no limit keyword or size-discovery fallback."""
    return _read_bounded(path,DEFAULT_LIMIT,private)


def reference_shape(ref,*,sized=True):
    return (type(ref) is dict and set(ref)==({'path','bytes','sha256'} if sized else {'path','sha256'})
            and canonical_path(ref['path']).is_absolute() and sha(ref['sha256'])
            and (not sized or type(ref['bytes']) is int and 0<ref['bytes']<=EXACT_LIMIT))


def read_reference(ref,*,private=True):
    need(reference_shape(ref),'F07_EXACT_SIZED_REFERENCE_REQUIRED')
    raw=_read_bounded(ref['path'],ref['bytes'],private)
    need(len(raw)==ref['bytes'] and digest(raw)==ref['sha256'],'F07_EXACT_REFERENCE_CHANGED'); return raw


# Preserve the already accepted direct/nested callback ABI. No F06 verdict is used.
read.f06_read_reference=read_reference
read.f07_read_reference=read_reference


def read_saved_reference(ref,*,private=True,known_large=None):
    """Real producers use 2ref or 3ref. A 2ref is default1MiB unless exact pinned
    (path,SHA) is explicitly listed in known_large. Never discover size or fallback.
    """
    if reference_shape(ref): return read_reference(ref,private=private)
    need(reference_shape(ref,sized=False),'F07_EXACT_PRODUCER_REFERENCE_REQUIRED')
    limits={} if known_large is None else known_large
    limit=limits.get((ref['path'],ref['sha256']),DEFAULT_LIMIT)
    raw=_read_bounded(ref['path'],limit,private)
    need(digest(raw)==ref['sha256'],'F07_PRODUCER_REFERENCE_CHANGED'); return raw


def doc(ref,*,private=True,known_large=None):
    return parse(read_saved_reference(ref,private=private,known_large=known_large))


def ref(path,*,private=True):
    raw=read(path,private=private)
    return dict(path=str(canonical_path(path)),bytes=len(raw),sha256=digest(raw))



def profile_config_refs():
    """Known-profile bounded snapshots; default read/ref ABI stays1MiB.
    Exact returned refs carry the observed bytes/SHA into final CAS and privacy.
    """
    configs={}
    for label,limit in PROFILE_CONFIG_LIMITS.items():
        path=DATABASES[label].parent/'config.yaml'
        raw=_read_bounded(path,limit,False)
        configs[label]=dict(path=str(canonical_path(path)),bytes=len(raw),sha256=digest(raw))
    return configs


def module(reference):
    need(reference_shape(reference),'DOCX225_PARENT_SOURCE_BINDING_UNBOUND')
    raw=read_reference(reference)
    value=types.ModuleType('_word_pinned_'+reference['sha256'][:12]); value.__file__=reference['path']
    exec(compile(raw,reference['path'],'exec'),value.__dict__); return value


def installation_shapes(closure,receipt,marker,stamp,inputs):
    need(closure.get('schema')=='frw.Root.native225.closed.v1'
         and closure.get('counts')==dict(base=17730,layers=225,native_files=17894,plugins=52,project_files=531)
         and closure.get('source_product_commit')==SOURCE_COMMIT
         and closure.get('state')=='INSTALLED225_AND_HEALTHY_DOCX_LOCATED_MAINSTORY_SEMANTICS_NOT_RUN_SEPARATE'
         and closure.get('no_next_operation_grant') is True,'DOCX225_ACTUAL_CLOSED_INSTALL_REQUIRED')
    need((len(receipt['layers']),len(receipt['files']),receipt['source_file_count'],len(marker['plugin_files']),len(inputs['project_files']))
         ==(225,17894,17730,52,531) and marker['source_receipt_sha256']==RECEIPT_SHA
         and marker['input_sha256']==INPUT_SHA and stamp['fridaySource']['layers']==receipt['layers']
         and stamp['fridaySource']['baseTree']==receipt['base_tree'],'DOCX225_CANONICAL_TUPLE_CHANGED')
    env=closure.get('installed_service_readback',{}).get('selected_environment')
    need(type(env) is dict and set(env)=={'gateway','dashboard'}
         and all(type(v) is dict and v.get('HERMES_HOME')==str(H) for v in env.values()),'DOCX225_ENVIRONMENT_BASIS_REQUIRED')
    return clone(env)


def effect_shape(effect):
    need(type(effect) is dict and set(effect)==EFFECT_FIELDS
         and effect.get('schema')=='frw.Root.DOCX225.current225-effect.v1','DOCX225_EXACT_EFFECT_REQUIRED')
    phase=effect['phase']; prep=module(PREP)
    prep.validate_preparation(phase)
    need(type(effect['run_id']) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',effect['run_id'])
         and effect['run_id']!='UNBOUND','DOCX225_NEW_RUN_UNBOUND')
    need(all(reference_shape(effect[k]) for k in ('authority','scenario','checker','source_preparation','installation_closure','source_acceptance')),
         'DOCX225_EXACT_EFFECT_REFS_UNBOUND')
    need(effect['source_preparation']==PREP and effect['checker']==ref(Path(__file__))
         and {k:effect['installation_closure'][k] for k in CLOSURE}==CLOSURE
         and {k:effect['source_acceptance'][k] for k in ACCEPTANCE}==ACCEPTANCE,
         'DOCX225_SELECTED_REVIEWED_SOURCE_OR_CLOSURE_CHANGED')
    need(read_reference(effect['scenario'])==encoded(phase['scenario']), 'DOCX225_EXACT_SINGLE_SCENARIO_REQUIRED')
    authority=doc(effect['authority'])
    base=read_saved_reference({'path':prep.SELECTED_TESTER,'sha256':SELECTED_SHA},private=False,
         known_large={(prep.SELECTED_TESTER,SELECTED_SHA):2*1024**2})
    prep.compose_source(base,phase,run_id=effect['run_id'],authority_ref=effect['authority'],authority=authority,
                        input_original=phase['input_original'])
    resources=effect['resources']
    need(type(resources) is dict and set(resources)==set(TIMING)|{'cpu_seconds','max_rss_bytes','disk_bytes','clock','owned_parent_wait_cleanup'}
         and all(type(resources[k]) is int and resources[k]==v for k,v in TIMING.items())
         and type(resources['cpu_seconds']) is int and 0<resources['cpu_seconds']<=120
         and type(resources['max_rss_bytes']) is int and 0<resources['max_rss_bytes']<=512*1024**2
         and type(resources['disk_bytes']) is int and 0<resources['disk_bytes']<=100*1024**2
         and reference_shape(resources['clock']) and reference_shape(resources['owned_parent_wait_cleanup']), 'DOCX225_FINITE_CONSUMER_RESOURCES_UNBOUND')
    clock=doc(resources['clock']); cleanup=doc(resources['owned_parent_wait_cleanup'])
    need(clock.get('schema')=='frw.Root.DOCX225.finite-operation-clock.v1'
         and clock.get('run_id')==effect['run_id'] and clock.get('scenario_sha256')==phase['scenario_sha256']
         and clock.get('timing')==TIMING and clock.get('status')=='ROOT_BOUND_FUTURE_OPERATION'
         and all(type(clock.get(k)) in (int,float) and math.isfinite(clock[k]) for k in ('started_monotonic','deadline_monotonic'))
         and clock['deadline_monotonic']-clock['started_monotonic']==TIMING['outer_seconds']
         and clock.get('old_effects_clocks_preserved') is True,'DOCX225_EXECUTABLE_OUTER_CLOCK_REQUIRED')
    need(cleanup.get('schema')=='frw.Root.DOCX225.owned-consumer-wait-cleanup.v1'
         and cleanup.get('run_id')==effect['run_id'] and cleanup.get('clock')==resources['clock']
         and cleanup.get('outer_seconds')==600 and cleanup.get('reserve_seconds')==5
         and cleanup.get('wait_same_owned_child') is True and cleanup.get('reap_before_release') is True
         and cleanup.get('no_detached_writer_or_retry') is True,'DOCX225_OWNED_PARENT_CLEANUP_REQUIRED')
    return authority,clock


def installation(effect):
    closure=doc(effect['installation_closure']);accepted=doc(effect['source_acceptance'])
    need(accepted.get('schema')=='frw.root.native225-source-acceptance.v1'
         and accepted.get('accepted') is True and accepted.get('execution_grant') is False
         and accepted.get('product_source_commit')==SOURCE_COMMIT
         and accepted.get('state')=='ROOT_ACCEPTED_EXACT225_DOCX_LOCATED_MAINSTORY_SOURCE_OFFLINE_NOT_RUNTIME',
         'DOCX225_EXACT_SOURCE_ACCEPTANCE_REQUIRED')
    rows=closure['actual_metadata'];canonical={k:rows[n] for k,n in dict(source_receipt='receipt',marker='marker',stamp='stamp',input='input').items()}
    values={k:doc(r,private=False) for k,r in canonical.items()}
    env=installation_shapes(closure,values['source_receipt'],values['marker'],values['stamp'],values['input'])
    need(canonical['source_receipt']['sha256']==RECEIPT_SHA and canonical['input']['sha256']==INPUT_SHA,'DOCX225_EXACT_RECEIPT_INPUT_REQUIRED')
    receipt=values['source_receipt'];marker=values['marker'];hashes={}
    for name in RELEVANT:
        expected=receipt['files'][name]['sha256']
        need(name not in LEAF_PINS or expected==LEAF_PINS[name],'DOCX225_ACCEPTED_NATIVE_DEPENDENCY_CHANGED')
        need(digest(read(H/'hermes-agent'/name,private=False))==expected,'DOCX225_CURRENT_NATIVE_SOURCE_CHANGED')
        hashes[name]=expected
    for name,want in marker['plugin_files'].items():
        need(type(name) is str and name and not Path(name).is_absolute() and str(Path(name))==name
             and all(p not in ('','.','..') for p in name.split('/')) and sha(want),'DOCX225_PLUGIN_PATH_REQUIRED')
        need(digest(read(H/name,private=False))==want,'DOCX225_INSTALLED_PLUGIN_CHANGED')
    return dict(canonical4=clone(canonical),runtime_hashes=hashes,environment_basis=env)


def process_bytes(pid,name):
    need(type(pid) is int and pid>0 and name in ('stat','cgroup','environ','cmdline'),'F07_BOUNDED_PROCESS_METADATA_ONLY')
    with (Path('/proc')/str(pid)/name).open('rb') as f: raw=f.read(DEFAULT_LIMIT+1)
    need(len(raw)<=DEFAULT_LIMIT,'F07_PROCESS_METADATA_OVERSIZE'); return raw


def kernel(pid):
    ticks=int(process_bytes(pid,'stat').rsplit(b')',1)[1].split()[19])
    return dict(pid=pid,start_time=ticks,boot_id=read_kernel_boot())


def read_kernel_boot():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def services(environment_basis):
    result={}; environments={}
    fields={'LoadState','ActiveState','SubState','MainPID','ControlPID','ControlGroup','InvocationID','UnitFileState','RuntimeMaxUSec','NRestarts'}
    selected={'HERMES_HOME','HERMES_GATEWAY_LOCK_DIR','HERMES_RUNTIME_DIR','HERMES_INSTALL_ROOT','HERMES_PROFILE'}
    for label,unit in [('gateway','hermes-gateway-1b7e7667.service'),('dashboard','hermes-dashboard.service')]:
        p=subprocess.run(['/usr/bin/systemctl','--user','show',unit,'--property='+','.join(sorted(fields))],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5,check=True)
        need(len(p.stdout)<=65536 and len(p.stderr)<=65536,'F07_SERVICE_METADATA_OVERSIZE')
        values=unique([line.split('=',1) for line in p.stdout.decode().splitlines()])
        need(set(values)==fields and all(values[k]==v for k,v in dict(LoadState='loaded',ActiveState='active',SubState='running',ControlPID='0',UnitFileState='enabled',RuntimeMaxUSec='infinity',NRestarts='0').items()),'F07_PERMANENT_SERVICE_UNHEALTHY')
        ident=kernel(int(values['MainPID']))
        need(('0::'+values['ControlGroup']).encode() in process_bytes(ident['pid'],'cgroup').splitlines(),'F07_SERVICE_CGROUP_CHANGED')
        env={k.decode():v.decode() for item in process_bytes(ident['pid'],'environ').split(b'\0')
             for k,sep,v in [item.partition(b'=')] if sep and k.decode() in selected}
        need(env==environment_basis[label],'F07_PER_SERVICE_EFFECTIVE_ENV_CHANGED')
        if label=='gateway':
            need(str(H/'hermes-agent').encode() in process_bytes(ident['pid'],'cmdline'),'F07_GATEWAY_SOURCE_ROOT_CHANGED')
        need(kernel(ident['pid'])==ident,'F07_SERVICE_KERNEL_CAS_CHANGED')
        result[label]=dict(identity=ident,invocation_id=values['InvocationID'],cgroup=values['ControlGroup'],runtime_max='infinity')
        environments[label]=env
    return result,environments


def pristine(row,effect,now):
    fields={'id','scenario','scenario_sha256','created_at','deadline','step','status','send_state','sent_ids','seen','message_ids','observations','update_count','last_text','repeat_count','send_attempts','capture_start_offset'}
    need(type(row) is dict and set(row)==fields and row['id']==effect['run_id']
         and row['scenario']==effect['phase']['scenario'] and row['scenario_sha256']==effect['phase']['scenario_sha256']
         and row['status']=='PREPARED' and row['send_state']=='none' and row['last_text'] is None
         and all(type(row[k]) is int and row[k]==0 for k in ('step','update_count','repeat_count','send_attempts'))
         and all(row[k]==[] for k in ('sent_ids','seen','message_ids','observations'))
         and type(row['capture_start_offset']) is int and row['capture_start_offset']>=0
         and type(row['deadline']) in (int,float) and now+195<=row['deadline']<=now+300,
         'F07_OWN_ROW_NOT_EXACT_PRISTINE_OR_FULL_WINDOW_LOST')
    created=dt.datetime.fromisoformat(row['created_at'])
    need(created.utcoffset() is not None and 0<=now-created.timestamp()<=120
         and abs(row['deadline']-created.timestamp()-300)<=1,'F07_OWN_PRISTINE_CREATION_CLOCK_CHANGED')


def history(effect,stage):
    root=canonical_path(STATE/'runs'); need(not root.is_symlink(),'F07_HISTORY_LINK')
    paths=sorted(root.iterdir()); need(len(paths)<=1025,'F07_HISTORY_COUNT_BOUND')
    records=[]; total=0; own=0
    for path in paths:
        need(path.suffix=='.json' and path.is_file(),'F07_HISTORY_UNEXPECTED_ENTRY')
        raw=read(path); total+=len(raw); need(total<=16*1024**2,'F07_HISTORY_AGGREGATE_BOUND')
        row=parse(raw); need(raw==encoded(row) and row.get('id')==path.stem,'F07_HISTORY_CANONICAL_CHANGED')
        if row['id']==effect['run_id']:
            pristine(row,effect,time.time()); own+=1; continue
        records.append([path.name,digest(raw),len(raw)])
    need(own==(1 if stage in ('CURSOR_AUTHORITY','PRE_INTENT_REVALIDATION') else 0),'F07_OWN_ABSENT_TO_PRISTINE_TRANSITION_REQUIRED')
    return dict(records=records,run_ids=[p[0][:-5] for p in records],sha256=digest(encoded(records)))


def custody():
    rows=[]
    def walk(parent):
        for path in sorted(parent.iterdir()):
            if path==STATE/'runs': continue
            need(not any(p.is_symlink() for p in (path,*path.parents)),'F07_CUSTODY_LINK')
            s=path.lstat()
            need(s.st_uid==os.getuid() and not stat.S_IMODE(s.st_mode)&0o002
                 and (stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode) and s.st_nlink==1)
                 and len(rows)<50000,'F07_CUSTODY_UNSAFE_OR_OVERSIZE')
            rows.append([str(path.relative_to(STATE)),list(identity(s))])
            if stat.S_ISDIR(s.st_mode): walk(path)
    walk(STATE); return dict(sha256=digest(encoded(rows)),records=rows,contents_read=False)


def databases():
    result={}; deadline=time.monotonic()+15
    for label,path in DATABASES.items():
        s=path.stat(); stable=identity(s)[:6]
        need(not any(p.is_symlink() for p in (path,*path.parents)) and stat.S_ISREG(s.st_mode)
             and s.st_uid==os.getuid() and s.st_nlink==1 and not stat.S_IMODE(s.st_mode)&0o002,'F07_DB_UNSAFE')
        with contextlib.closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=1)) as db:
            db.set_progress_handler(lambda:int(time.monotonic()>=deadline),1000)
            db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
            check=db.execute('PRAGMA quick_check').fetchone()[0]
            leases=db.execute('SELECT count(*) FROM session_turn_leases').fetchone()[0]
            pending=db.execute("SELECT count(*) FROM async_delegations WHERE state IN ('running','stalling','finalizing') OR delivery_state IN ('pending','claimed','deferred')").fetchone()[0]
            count=db.execute('SELECT count(*) FROM messages').fetchone()[0]
            need(type(count) is int and 0<=count<=100000,'F07_DB_METADATA_COUNT_BOUND')
            sessions=db.execute('SELECT '+','.join(SESSION_FIELDS)+' FROM sessions ORDER BY id').fetchall()
            rows=db.execute('SELECT '+','.join(MESSAGE_FIELDS)+' FROM messages ORDER BY id').fetchall(); db.rollback()
        need(check=='ok' and leases==pending==0 and len(rows)==count and len(sessions)<=10000
             and identity(path.stat())[:6]==stable,'F07_ALL3_SQL_NOT_QUIESCENT_OR_CAS_CHANGED')
        spool=path.parent/'pending_messages'; need(not os.path.lexists(spool) or not spool.is_symlink() and spool.is_dir() and not list(spool.iterdir()),'F07_PENDING_SPOOL_PRESENT')
        value=dict(identity=list(stable),messages=count,max_message_id=max((row[0] for row in rows),default=None),sessions=len(sessions),leases=leases,all_origin_pending_delegations=pending,metadata_sha256=digest(encoded(dict(sessions=sessions,messages=rows))))
        if label=='tester':
            found=[dict(zip(SESSION_FIELDS,row)) for row in sessions if row[0]==SID]
            need(found==[PRINCIPAL],'F07_NATIVE_TESTER_PRINCIPAL_CHANGED'); value['principal']=PRINCIPAL
        result[label]=value
    return result


def technical_log_cursor():
    rows={}
    for name in ('agent.log','gateway.log'):
        path=H/'profiles/telegram-bot-8812646969/logs'/name
        need(not any(p.is_symlink() for p in (path,*path.parents)),'F07_LOG_LINK')
        s=path.stat(); need(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and not stat.S_IMODE(s.st_mode)&0o002,'F07_LOG_CUSTODY_UNSAFE')
        rows[str(path)]=list(identity(s))
    return dict(schema='frw.Root.DOCX225.technical-log-metadata-cursor.v1',files=rows,contents_read=False)


def stable_native(native):
    result=clone(native); result.get('global_work',{}).pop('observed_monotonic',None); return result


def observe(effect,*,stage='BASELINE'):
    """EXPLICIT FUTURE ROOT CALL. Never invoked by child source/offline controls."""
    effect_shape(effect)
    return _observe_current(effect,stage=stage)


def observe_readonly(*,phase,run_id,closure_ref,acceptance_ref,resource_limits):
    """Explicit future Root metadata collection. No authority or clock issuance."""
    prep=module(PREP); prep.validate_preparation(phase)
    need(type(run_id) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',run_id)
         and run_id!='UNBOUND','DOCX225_READONLY_EXACT_SELECTED_RUN_REQUIRED')
    need(reference_shape(closure_ref) and {k:closure_ref[k] for k in CLOSURE}==CLOSURE
         and reference_shape(acceptance_ref) and {k:acceptance_ref[k] for k in ACCEPTANCE}==ACCEPTANCE,
         'DOCX225_READONLY_EXACT225_INSTALLATION_BASIS_REQUIRED')
    need(type(resource_limits) is dict and set(resource_limits)=={'max_rss_bytes','disk_bytes'}
         and all(type(v) is int and v>0 for v in resource_limits.values())
         and resource_limits['max_rss_bytes']<=512*1024**2 and resource_limits['disk_bytes']<=100*1024**2,
         'DOCX225_READONLY_RESOURCE_PREDICATES_REQUIRED')
    inputs=dict(run_id=run_id,phase=clone(phase),installation_closure=clone(closure_ref),source_acceptance=clone(acceptance_ref),resources=clone(resource_limits))
    return dict(state='READONLY_CURRENT_FACTS_NOT_OPERATION_ADMISSION',operation_clock_created=False,
                authority_issued=False,observed=_observe_current(inputs,stage='BASELINE'))


def original_source_current(source):
    prep=module(PREP);prep.validate_input(source);path=canonical_path(source['path'])
    need(not any(p.is_symlink() for p in (path,*path.parents)), 'DOCX225_SOURCE_LINK')
    with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
        before=os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1
             and not stat.S_IMODE(before.st_mode)&0o077,'DOCX225_SOURCE_CUSTODY_CHANGED')
        raw=stream.read(prep.SOURCE_BYTES+1);after=os.fstat(stream.fileno());current=path.stat()
        actual=dict(device=before.st_dev,inode=before.st_ino,size_bytes=before.st_size,
                    uid=before.st_uid,mtime_ns=before.st_mtime_ns,ctime_ns=before.st_ctime_ns)
        need(len(raw)==prep.SOURCE_BYTES and digest(raw)==prep.SOURCE_SHA and actual==source['stat']
             and identity(before)==identity(after)==identity(current),'DOCX225_SOURCE_FD_STAT_HASH_CAS_CHANGED')
    return dict(source_reference={k:source[k] for k in ('path','bytes','sha256')},source_stat=actual,
                identity=list(identity(before)),source_kind=prep.SOURCE_KIND,upload_or_receiver_custody_claimed=False)


NATIVE_PYTHON = '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/installs/45eb40fd2d5351a9/environments/8e0c92ce48434ddbb9125ee001560ccb/venv/bin/python'
NATIVE_SITE_PACKAGES = (Path(NATIVE_PYTHON).parent.parent/'lib')/('python'+str(sys.version_info.major)+'.'+str(sys.version_info.minor))/'site-packages'


def permission_current():
    """Future Root only: exact native readonly APIs, including sticky capability.

    PluginState ctor only binds names; directory_storage_readonly and
    get_storage_readonly use the existing repair=False API. No data_dir, writer,
    provisioning, token read, model call or user-supplied source is invoked.
    """
    need(sys.dont_write_bytecode is True,'DOCX225_NATIVE_IMPORT_REQUIRES_B_MODE')
    native=H/'hermes-agent'
    site=NATIVE_SITE_PACKAGES
    # Use the existing installed native consumer interpreter; globalvenv lacks ruamel. -I/-S are retained;
    # append its explicit package directory without executing .pth/site hooks.
    for path in (native,site):
        need(not any(p.is_symlink() for p in (path,*path.parents)) and path.is_dir(),
             'DOCX225_EXPLICIT_NATIVE_IMPORT_ROOT_REQUIRED')
    previous=list(sys.path)
    try:
        sys.path[:0]=[str(native),str(site)]
        scope=importlib.import_module('hermes_cli.friday_user_scope')
        access=importlib.import_module('hermes_cli.friday_product_access')
        statecode=importlib.import_module('hermes_cli.plugins_state')
        for code,name in ((scope,'hermes_cli/friday_user_scope.py'),(access,'hermes_cli/friday_product_access.py'),
                          (statecode,'hermes_cli/plugins_state.py')):
            need(Path(code.__file__)==native/name and digest(read(code.__file__,private=False))==LEAF_PINS[name],
                 'DOCX225_EXACT_NATIVE_PERMISSION_SOURCE_REQUIRED')
        before=profile_config_refs();home=H/'profiles'/PRINCIPAL['profile_name'];home_info=home.stat()
        with scope.authority(H):
            isolation=scope.policy(H);policy=access.access_policy()
            state=statecode.PluginState('friday_rework')
            directory=state.directory_storage_readonly
            statepath=directory/'state.json';state_info=statepath.stat()
            admitted=access.current_access(state)
        key=access.principal_id('telegram',PRINCIPAL['transport_profile'],'8751854128',PRINCIPAL['user_id'])
        bindings=[] if isolation is None else [r for r in isolation['bindings']
            if access.principal_id(*(r[k] for k in ('platform','transport_profile','account_id','user_id')))==key]
        need(len(bindings)==1 and bindings[0]['runtime_profile']==PRINCIPAL['profile_name']
             and {'read_file','write_file'}<=set(bindings[0]['tools']),'DOCX225_NATIVE_READ_WRITE_SCOPE_NOT_GRANTED')
        accounts=[] if policy is None else [r for r in policy['accounts'] if
            (r['platform'],r['transport_profile'],r['account_id'])==('telegram',PRINCIPAL['transport_profile'],'8751854128')]
        row=admitted['users'].get(key)
        need(len(accounts)==1 and PRINCIPAL['profile_name'] in accounts[0]['runtime_profiles']
             and type(row) is dict and row.get('enabled') is True
             and type(row.get('generation')) is int and row['generation']>=1,'DOCX225_CURRENT_NATIVE_ACCESS_DISABLED_OR_CHANGED')
        proposed=scope.UserScope(H,home,PRINCIPAL['profile_name'],('telegram',PRINCIPAL['transport_profile'],'8751854128',PRINCIPAL['user_id']),
                            clone(bindings[0]),(home_info.st_dev,home_info.st_ino),row['generation'])
        # A local proposed object qualifies current policy/home only. It is never
        # installed into _CURRENT/_SOURCE or attached to a TG event/agent.
        with scope.authority(home):proposed.check()
        marker=ref(home/scope.MARKER)
        with scope.authority(H):
            need(scope.policy(H)==isolation and access.access_policy()==policy
                 and access.current_access(state)==admitted and state.directory_storage_readonly==directory,
                 'DOCX225_NATIVE_PERMISSION_SEMANTIC_CAS_CHANGED')
        need(profile_config_refs()==before and identity(home.stat())==identity(home_info)
             and identity(statepath.stat())==identity(state_info),'DOCX225_NATIVE_PERMISSION_FILE_CAS_CHANGED')
        return dict(schema='frw.Root.DOCX225.native-readonly-permission.v1',
            state='PREFLIGHT_POLICY_NAMESPACE_ONLY_NOT_NATIVE_EVENT_AUTHORITY',
            planned_principal_only=True,new_Telegram_event_capability_issued=False,principal_key=key,
            runtime_profile=PRINCIPAL['profile_name'],admission_generation=row['generation'],
            binding_sha256=digest(encoded(bindings[0])),access_policy_sha256=digest(encoded(policy)),
            access_document_sha256=digest(encoded(admitted)),state_identity=list(identity(state_info)),
            home_identity=list(identity(home_info)),scope_marker=marker,profile_configs=before,
            native_capability_check=True,read_file_and_write_file=True,readonly=True)
    finally:
        sys.path[:]=previous


def source_scope_current(scope):
    prep=module(PREP);root=canonical_path(scope['workspace_root']);destination=canonical_path(scope['destination_path'])
    need(scope['principal']==PRINCIPAL and scope['source_kind']==prep.SOURCE_KIND
         and root==H/'profiles'/PRINCIPAL['profile_name']/'workspace',
         'DOCX225_OWN_PRINCIPAL_PRODUCT_WORKSPACE_REQUIRED')
    need(not any(p.is_symlink() for p in (root,*root.parents)), 'DOCX225_WORKSPACE_LINK')
    info=root.stat()
    need(stat.S_ISDIR(info.st_mode) and info.st_uid==os.getuid() and not stat.S_IMODE(info.st_mode)&0o077,
         'DOCX225_PROTECTED_WORKSPACE_REQUIRED')
    need(destination==root/prep.OUTPUT_NAME and not os.path.lexists(destination),'DOCX225_CREATE_ONLY_DESTINATION_NOT_ABSENT')
    evidence=[]
    for r in scope['access_evidence']:read_reference(r);evidence.append(clone(r))
    return dict(workspace_root=str(root),workspace_identity=list(identity(info)),destination=str(destination),
                destination_absent=True,principal=clone(PRINCIPAL),source_kind=prep.SOURCE_KIND,access_evidence=evidence,
                product_access_semantics='ROOT_EXPLICIT_CURRENT_DECISION_REQUIRED')


def _observe_current(effect,*,stage):
    """Shared readonly machinery; only validated explicit public entry calls it."""
    for path in (H,STATE):
        s=path.stat()
        need(not any(p.is_symlink() for p in (path,*path.parents)) and stat.S_ISDIR(s.st_mode)
             and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700,'F07_PROTECTED_HOME_OR_TESTER_CUSTODY_CHANGED')
    installed=installation(effect)
    service_rows,env=services(installed['environment_basis'])
    raw=read(H/'gateway_state.json',private=False); state=parse(raw); tg=state.get('platforms',{}).get('telegram',{})
    need(state.get('gateway_state')=='running' and state.get('active_agents')==0 and state.get('active_work') is None
         and state.get('restart_requested') is False and state.get('session_store',{}).get('status')=='ok'
         and state.get('served_profiles')==['default','dest_telegram','telegram-bot-8812646969'] and state.get('hermes_home')==str(H)
         and state.get('argv')==[str(H/'hermes-agent/hermes_cli/main.py'),'gateway','run']
         and tg.get('state')=='connected' and tg.get('needs_attention') is False
         and tg.get('writer_pid')==state.get('pid') and tg.get('writer_start_time')==state.get('start_time'), 'F07_CURRENT_GATEWAY_NOT_QUIESCENT')
    ident=kernel(state['pid']); need(ident['start_time']==state['start_time'] and service_rows['gateway']['identity']==ident,'F07_GATEWAY_KERNEL_MISMATCH')
    latest=max(max(s.st_mtime_ns,s.st_ctime_ns) for name in RELEVANT for s in [(H/'hermes-agent'/name).stat()])
    born=time.time()-float(Path('/proc/uptime').read_text().split()[0])+ident['start_time']/os.sysconf('SC_CLK_TCK')
    need(born*1e9>latest,'F07_GATEWAY_PREDATES_ACCEPTED_CURRENT_NATIVE_SOURCE')
    transport=module(TRANSPORT); native=transport.fresh_native(state)
    need(native['identity']==ident and native['quiescent'] is True and native['global_work']['global_active_session_keys']==[],'F07_GLOBAL_NATIVE_NOT_QUIESCENT')
    dbs=databases(); hist=history(effect,stage); owned=custody()
    cursor=ref(STATE/'cursor.json'); cur=doc(cursor)
    need(type(cur.get('offset')) is int and cur['offset']>=0,'F07_CURSOR_INVALID')
    need(not os.path.lexists(STATE/'observer-stop.json'),'F07_OBSERVER_CANCELLED')
    cooldown=ref(STATE/'cooldown.json') if os.path.lexists(STATE/'cooldown.json') else None
    until=doc(cooldown).get('until',0) if cooldown else 0
    need(type(until) in (int,float) and math.isfinite(until) and until<=time.time(),'F07_ACTIVE_COOLDOWN')
    need(not os.path.lexists(H/'maintenance.json'),'F07_MAINTENANCE_PRESENT')
    source=effect['phase']['input_original']
    original=original_source_current(source)
    permission=permission_current()
    runtime=source_scope_current(effect['phase']['source_scope'])
    info=canonical_path(source['path']).stat(); actual_stat=original['source_stat']
    configs=profile_config_refs()
    logs=technical_log_cursor()
    need(read(H/'gateway_state.json',private=False)==raw and kernel(ident['pid'])==ident
         and services(installed['environment_basis'])==(service_rows,env),'F07_SERVICE_OR_STATE_CAS_CHANGED')
    need(databases()==dbs and history(effect,stage)==hist and custody()==owned
         and ref(STATE/'cursor.json')==cursor and technical_log_cursor()==logs
         and profile_config_refs()==configs,
         'F07_FINAL_SQL_HISTORY_ONCE_CURSOR_CONFIG_OR_LOG_CAS_CHANGED')
    need(original_source_current(source)==original
         and identity(canonical_path(source['path']).stat())==identity(info),
         'DOCX225_FINAL_ORIGINAL_INPUT_CAS_CHANGED')
    need(permission_current()==permission,'DOCX225_FINAL_NATIVE_PERMISSION_CHANGED')
    need(source_scope_current(effect['phase']['source_scope'])==runtime,
         'DOCX225_FINAL_SELECTED_RUNTIME_CAS_CHANGED')
    # Refresh native after allSQL/source/once reads; only transient timestamps differ.
    final=transport.fresh_native(state)
    need(stable_native(final)==stable_native(native),'F07_NATIVE_GENERATION_OR_CUSTODY_CHANGED')
    mem={k:int(v.split()[0]) for line in Path('/proc/meminfo').read_text().splitlines() for k,_,v in [line.partition(':')]}
    disk=os.statvfs(STATE)
    need(mem['MemAvailable']*1024>=effect['resources']['max_rss_bytes']
         and disk.f_bavail*disk.f_frsize>=effect['resources']['disk_bytes'] and bool(os.sched_getaffinity(0)),
         'F07_CURRENT_RESOURCES_INSUFFICIENT')
    return dict(schema='frw.Root.DOCX225.current225-observation.v1',installed=installed,services=service_rows,process_environment=env,gateway=ident,native=stable_native(final),databases=dbs,history=hist,custody=owned,cursor=cursor,cooldown=cooldown,source_stat=actual_stat,original_source=original,source_scope=runtime,permission=permission,profile_configs=configs,technical_log_cursor=logs,projection_limit=PROJECTION_LIMIT)


def fresh(proof,*,wall=None,mono=None):
    wall=time.time() if wall is None else wall; mono=time.monotonic() if mono is None else mono
    need(all(type(proof.get(k)) in (int,float) and math.isfinite(proof[k]) for k in ('created_at','expires_at','created_monotonic','expires_monotonic')),'F07_FINITE_PROOF_CLOCK_REQUIRED')
    need(0<=proof['created_at']<=wall<proof['expires_at']<=proof['created_at']+120
         and 0<=proof['created_monotonic']<=mono<proof['expires_monotonic']<=proof['created_monotonic']+120,'F07_EXPIRED_OR_FUTURE_PROOF')
    return min(proof['expires_monotonic'],mono+proof['expires_at']-wall)


def lock_held(path,owner):
    need(type(owner) is dict and set(owner)=={'pid','start_time','boot_id'} and kernel(owner['pid'])==owner,'F07_LOCK_OWNER_CHANGED')
    p=canonical_path(path); s=p.stat()
    need(not any(q.is_symlink() for q in (p,*p.parents)) and stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600,'F07_LOCK_CUSTODY_CHANGED')
    device=f'{os.major(s.st_dev):02x}:{os.minor(s.st_dev):02x}:{s.st_ino}'
    need(any(len(v:=row.split())>=6 and v[1]=='FLOCK' and v[3]=='WRITE' and v[4]==str(owner['pid']) and v[5]==device for row in Path('/proc/locks').read_text().splitlines()),'F07_EXCLUSIVE_NAMED_LOCK_NOT_HELD')


def decisions(proof,actual,proof_ref):
    effect=proof['effect']; review=doc(proof['Root_decision']); privacy=doc(proof['privacy_preflight'])
    need(review.get('schema')=='frw.Root.DOCX225.current225-original-case-decision.v1'
         and review.get('operator')=='Root' and review.get('status')=='ROOT_BOUND'
         and review.get('whole_effect_sha256')==proof['whole_effect_sha256']
         and review.get('history_sha256')==actual['history']['sha256'] and review.get('custody_sha256')==actual['custody']['sha256']
         and review.get('native_SQL_boundary_sha256')==digest(encoded(dict(native=actual['native'],databases=actual['databases'])))
         and review.get('original_F03_BODYedit_effect_eligible') is True and review.get('old_effects_UNKNOWN_clocks_preserved') is True
         and review.get('exact_F03_source_domain_effects_reconciled') is True
         and review.get('equivalent_consumed_F03_BODYedit_effects')==[]
         and review.get('effect_domain')==module(PREP).effect_domain(effect['phase'])
         and review.get('projection_limit')==PROJECTION_LIMIT
         and review.get('root_current_pending_approval_cancel_maintenance_assessed') is True
         and review.get('root_current_product_access_permission_source_scope_eligible') is True
         and review.get('root_current_cancel_recovery_user_isolation_eligible') is True,
         'DOCX225_EXACT_ROOT_ORIGINAL_FORWARD_CURRENT_DECISION_UNBOUND')
    evidence=review.get('current_scope_evidence'); need(type(evidence) is list and bool(evidence),'F07_ROOT_BROAD_SCOPE_EVIDENCE_REQUIRED')
    for r in evidence: read_reference(r)
    need(privacy.get('schema')=='frw.Root.DOCX225.current225-privacy-preflight.v1'
         and privacy.get('operator')=='Root' and privacy.get('status')=='ROOT_BOUND_PREFLIGHT_NOT_RUNTIME_VERDICT'
         and privacy.get('whole_effect_sha256')==proof['whole_effect_sha256']
         and privacy.get('runtime_hashes')==actual['installed']['runtime_hashes']
         and privacy.get('logging_sites')==list(LOGGING_SITES)
         and privacy.get('technical_log_cursor')==actual['technical_log_cursor']
         and privacy.get('postcondition_plan')==postcondition_plan(effect,actual)
         and privacy.get('source_metadata_only_checked') is True
         and privacy.get('genuine_current_event_observed') is False
         and privacy.get('runtime_logging_verdict')=='NOT_ESTABLISHED'
         and privacy.get('raw_user_retention_separately_scoped') is True,'F07_PRIVACY_PREFLIGHT_UNBOUND_OR_FUTURE_VERDICT')
    evidence=privacy.get('source_evidence'); need(type(evidence) is list and bool(evidence),'F07_PRIVACY_SOURCE_BASIS_REQUIRED')
    for r in evidence: read_reference(r)
    roots=privacy.get('effective_product_roots'); protected=privacy.get('private_roots')
    need(type(roots) is list and roots==sorted(set(roots)) and str(H) in roots
         and type(protected) is list and protected==sorted(set(protected)) and bool(protected),
         'F07_SOURCE_DERIVED_PRODUCT_AND_PRIVATE_ROOTS_REQUIRED')
    for p in protected:
        private=canonical_path(p); info=private.stat()
        need(not any(q.is_symlink() for q in (private,*private.parents)) and stat.S_ISDIR(info.st_mode)
             and info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o700,'F07_PRIVATE_ROOT_CUSTODY_CHANGED')
        need(all(not private.is_relative_to(canonical_path(root)) and not canonical_path(root).is_relative_to(private)
                 for root in roots),'F07_PRIVATE_ROOT_INTERSECTS_PRODUCT')
    materials=[effect[k]['path'] for k in ('authority','scenario','checker','source_preparation','installation_closure','source_acceptance')]
    materials += [effect['resources'][k]['path'] for k in ('clock','owned_parent_wait_cleanup')]
    materials += [proof[k]['path'] for k in ('Root_decision','privacy_preflight','invocation')]+[proof_ref['path']]
    materials += [r['path'] for r in effect['phase']['source_scope']['access_evidence']]
    # Product source is scoped user data, never a private authority/oracle material.
    source=canonical_path(effect['phase']['input_original']['path']);scope=actual['source_scope']
    need(str(source.parent)==scope['workspace_root'] and scope['source_kind']=='OWN_USER_WORKSPACE_NATIVE_OUTPUT_NOT_RECEIVED',
         'DOCX225_EXACT_RETAINED_NATIVE_SOURCE_SCOPE_REQUIRED')
    need(all(any(canonical_path(path).is_relative_to(canonical_path(root)) for root in protected) for path in materials),
         'F07_PRIVATE_MATERIAL_ROOT_COVERAGE_REQUIRED')
    need(privacy.get('effective_roots_profile_config_refs')==actual['profile_configs'],
         'F07_CURRENT_CONFIG_ROOTS_BASIS_CHANGED')
    basis=privacy.get('effective_roots_source_basis'); need(type(basis) is list and bool(basis),'F07_ROOTS_CONSUMER_BASIS_REQUIRED')
    for r in basis: read_reference(r)
    markers=[p.encode() for p in protected]
    for r in actual['profile_configs'].values():
        need(not any(p in read_reference(r,private=False) for p in markers),'F07_PRIVATE_ROOT_IN_PRODUCT_CONFIG')
    for name in ('cmdline','environ'):
        need(not any(p in process_bytes(actual['gateway']['pid'],name) for p in markers),'F07_PRIVATE_ROOT_IN_GATEWAY_PROCESS')


def check(proof_ref,*,run_id,scenario,stage):
    """Existing ordinary.new / _send pre-intent hook; returns no grant.
    Root binds every actual field after reconciling original F03 same-source BODY-edit eligibility.
    No aftersameoperation output, ACK, model grade or future source_ref is required.
    """
    proof=doc(proof_ref)
    need(type(proof) is dict and set(proof)==PROOF_FIELDS and proof.get('schema')=='frw.Root.DOCX225.current225-preintent.v1'
         and proof.get('status')=='ROOT_BOUND' and proof.get('operator')=='Root','F07_CURRENT_ROOT_PROOF_UNBOUND')
    deadline=fresh(proof); effect=proof['effect']; _,clock=effect_shape(effect)
    need(proof['whole_effect_sha256']==digest(encoded(effect)) and proof['boot_id']==read_kernel_boot()
         and run_id==effect['run_id'] and scenario==effect['phase']['scenario']
         and stage in ('NEW','CURSOR_AUTHORITY','PRE_INTENT_REVALIDATION'),'F07_PREINTENT_EFFECT_OR_STAGE_CHANGED')
    need(set(proof['lock_owners'])=={'shared_slot','consumer','credential'},'F07_ALL_NAMED_LOCK_OWNERS_REQUIRED')
    for label,path in dict(shared_slot=SLOT,consumer=STATE/'consumer.lock',credential=STATE/'tester-token').items(): lock_held(path,proof['lock_owners'][label])
    actual=observe(effect,stage=stage)
    need(actual==proof['observed'],'F07_MUTABLE_CURRENT_FACTS_CHANGED')
    invocation=doc(proof['invocation'])
    need(invocation.get('schema')=='frw.Root.DOCX225.one-ordinary-consumer-invocation.v1'
         and invocation.get('run_id')==run_id and invocation.get('whole_effect_sha256')==proof['whole_effect_sha256']
         and invocation.get('clock')==effect['resources']['clock'] and invocation.get('no_retry') is True
         and invocation.get('consumer')==kernel(os.getpid())
         and proof['lock_owners']['consumer']==proof['lock_owners']['credential']==invocation['consumer'],
         'F07_EXISTING_ONCE_INVOCATION_OR_CONSUMER_IDENTITY_REQUIRED')
    decisions(proof,actual,proof_ref)
    need(resource.getrlimit(resource.RLIMIT_CPU)[0] not in (-1,resource.RLIM_INFINITY)
         and 0<resource.getrlimit(resource.RLIMIT_CPU)[0]<=effect['resources']['cpu_seconds']
         and resource.getrlimit(resource.RLIMIT_AS)[0] not in (-1,resource.RLIM_INFINITY)
         and 0<resource.getrlimit(resource.RLIMIT_AS)[0]<=effect['resources']['max_rss_bytes'], 'F07_CONSUMER_CPU_AS_LIMITS_NOT_APPLIED')
    need(resource.getrlimit(resource.RLIMIT_FSIZE)[0] not in (-1,resource.RLIM_INFINITY)
         and 0<resource.getrlimit(resource.RLIMIT_FSIZE)[0]<=effect['resources']['disk_bytes'],
         'F07_CONSUMER_FILESIZE_LIMIT_NOT_APPLIED')
    need(time.monotonic()+195<clock['deadline_monotonic'] and time.monotonic()<deadline,'F07_OUTER_RESERVE_OR_PROOF_EXPIRED')
    fresh(proof)
    return dict(admission=False,state='CURRENT225_PREINTENT_CHECKED_NOT_PRODUCT_ACCEPTANCE',whole_effect_sha256=proof['whole_effect_sha256'],stage=stage)


def postcondition_plan(effect,observed):
    phase=effect['phase'];capture=phase['scenario']['steps'][0]['observe']
    return dict(schema='frw.Root.DOCX225.actual-postcondition-plan.v1',run_id=effect['run_id'],
        original_case='F03/structuredDOCX/singleBODYdeadline22to23',scenario_sha256=phase['scenario_sha256'],
        whole_effect_sha256=digest(encoded(effect)),installation_closure=effect['installation_closure'],
        gateway=observed['gateway'],native_principal=PRINCIPAL,baseline_databases=observed['databases'],
        technical_log_cursor=observed['technical_log_cursor'],runtime_hashes=observed['installed']['runtime_hashes'],
        source_scope=observed['source_scope'],input_original=phase['input_original'],logging_sites=list(LOGGING_SITES),
        saved_byte_evaluator=clone(SEMANTIC_EVALUATOR),source_leaves_acceptance=clone(SOURCE_LEAVES_ACCEPTANCE),
        expected_semantics=phase['expected_semantics'],capture=dict(full_seconds=capture['window_seconds'],
        max_updates=phase['scenario']['max_updates'],max_messages=capture['max_messages'],
        max_documents=capture['max_documents'],document_max_bytes=capture['document_max_bytes'],ack_seconds=10),
        exact_one_delivered_native_DOCX_required_after_send=True,source_preservation_required_after_send=True,
        genuine_first_document_upload_required=False,source_kind='OWN_USER_WORKSPACE_NATIVE_OUTPUT_NOT_RECEIVED',
        same_actual_file_assessment_no_producer_replay=True,future_output_required_preintent=False,
        raw_statuses_preserved=True,no_extra_event_or_replay=True)


def prepare_effect(*,run_id,phase,authority_ref,scenario_ref,checker_ref,closure_ref,acceptance_ref,resources):
    """Pure composition of Root-supplied bindings; returns no authority/proof."""
    need(all(reference_shape(r) for r in (authority_ref,scenario_ref,checker_ref,closure_ref,acceptance_ref)),
         'F07_ROOT_SIZED_BINDINGS_REQUIRED')
    return dict(schema='frw.Root.DOCX225.current225-effect.v1',run_id=run_id,phase=clone(phase),authority=clone(authority_ref),
                scenario=clone(scenario_ref),checker=clone(checker_ref),source_preparation=clone(PREP),
                installation_closure=clone(closure_ref),source_acceptance=clone(acceptance_ref),resources=clone(resources))






def compose_preintent_source(composed_raw,*,phase,run_id,authority_ref,authority,proof_ref,checker_ref,input_original=None):
    """Insert one exact checker into the selected original admission method.
    Source preparation preserves original ACK10, genuine document API, intent and history contracts.
    No NEW/save/Store/API/operation is executed by this pure composition.
    """
    prep=module(PREP)
    need(reference_shape(proof_ref) and checker_ref==ref(Path(__file__)),'DOCX225_EXACT_FUTURE_ROOT_PROOF_AND_CHECKER_REQUIRED')
    prep.validate_preparation(phase)
    need(input_original is None or input_original==phase['input_original'],'DOCX225_ORIGINAL_INPUT_CHANGED')
    base=read_saved_reference({'path':prep.SELECTED_TESTER,'sha256':SELECTED_SHA},private=False,known_large={(prep.SELECTED_TESTER,SELECTED_SHA):2*1024**2})
    need(composed_raw==prep.compose_source(base,phase,run_id=run_id,authority_ref=authority_ref,authority=authority,
            input_original=phase['input_original']),'DOCX225_FROZEN_SINGLE_CASE_COMPOSITION_CHANGED')
    tree=ast.parse(composed_raw)
    runners=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Runner']
    need(len(runners)==1,'DOCX225_EXACT_RUNNER_REQUIRED')
    methods=[n for n in runners[0].body if isinstance(n,ast.FunctionDef) and n.name=='ordinary_independent_admission']
    need(len(methods)==1 and bool(methods[0].body),'DOCX225_EXACT_ADMISSION_METHOD_REQUIRED')
    method=methods[0];lines=composed_raw.decode().splitlines(keepends=True)
    code=("        if name == "+repr(run_id)+":\n"
        "            _word_ref = "+repr(checker_ref)+"\n"
        "            _word_raw = safe_read(Path(_word_ref['path']))\n"
        "            if len(_word_raw) != _word_ref['bytes'] or digest(_word_raw) != _word_ref['sha256']:\n"
        "                raise Refused('DOCX225 exact current225 checker changed')\n"
        "            import types as _word_types\n"
        "            _word = _word_types.ModuleType('_Root_DOCX225_current225')\n"
        "            _word.__file__ = _word_ref['path']\n"
        "            exec(compile(_word_raw, _word.__file__, 'exec'), _word.__dict__)\n"
        "            _word.check("+repr(proof_ref)+", run_id=name, scenario=scenario,\n"
        "                                stage=getattr(self, '_send_phase', 'NEW'))\n")
    lines[method.body[0].lineno-1:method.body[0].lineno-1]=[code]
    result=''.join(lines).encode(); ast.parse(result); return result


def unbound_proof():
    return dict(schema='frw.Root.DOCX225.current225-preintent.v1',status='UNBOUND_NOT_GRANTED',operator='Root',effect=None,whole_effect_sha256=None,created_at=None,expires_at=None,created_monotonic=None,expires_monotonic=None,boot_id=None,observed=None,lock_owners=None,invocation=None,Root_decision=None,privacy_preflight=None)


if __name__=='__main__':
    raise SystemExit('SOURCE ONLY: Root must explicitly bind genuine current evidence before check')
