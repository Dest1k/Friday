"""Fixed228 metadata-only Source sibling for explicit future Root callers.

CLOSURE is Root's pinned, small, dated Source normalization, not raw closure or
current authority. Generic read/permission/service/identity/CAS helpers retain
the accepted parent implementations. No IO at import. This module has no
ordinary-admission entrypoint: check/observe/installation always refuse.
Actual canonical values, fresh current rights, history, cancellation and all
ordinary operation guards remain separate mandatory Root/caller checks.
"""


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


PROJECTION_LIMIT = 'ALL_PROFILE_IN_MEMORY_PENDING_QUEUES_APPROVALS_NOT_EXPOSED'


SESSION_FIELDS = ('id','source','user_id','chat_id','chat_type','session_key','profile_name','transport_profile')


MESSAGE_FIELDS = ('id','session_id','role','timestamp','platform_message_id','active','compacted')


PRINCIPAL = dict(id=SID,source='telegram',user_id='8812646969',chat_id='8812646969',chat_type='dm',session_key=KEY,profile_name='telegram-bot-8812646969',transport_profile='default')


DATABASES = {'default':H/'state.db','dest':H/'profiles/dest_telegram/state.db','tester':H/'profiles/telegram-bot-8812646969/state.db'}


PROFILE_CONFIG_LIMITS = {'default':4*1024**2,'dest':DEFAULT_LIMIT,'tester':4*1024**2}


NATIVE_PYTHON = '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/installs/45eb40fd2d5351a9/environments/8e0c92ce48434ddbb9125ee001560ccb/venv/bin/python'


NATIVE_SITE_PACKAGES = None


SOURCE_BOUND = True


METADATA_ONLY = True


PARENT_SOURCE = {'path': '/home/jericho/.cache/FRW-ASTRA-DOCX226-SUMMARY-SOURCE-BIND-20261116/bound-source-r1/docx_summary_recall_current.py', 'bytes': 65678, 'sha256': 'a1a3f7aa1a9d2c68ed8034188831e3798b29c750eebaf03de494afe214ce069f'}


CLOSURE = {'bytes': 4001, 'path': '/home/jericho/.cache/FRW-ASTRA-FIXED228-METADATA-SIBLING-SOURCE-20261117/ROOT-ACTUAL228-INSTALLATION-METADATA-SOURCE.json', 'sha256': '85e57d286100228d0e8059ffdb68c762526013c4f75fafa99268bcaeee4fa42a'}


ACCEPTANCE = {'bytes': 5903, 'path': '/home/jericho/.cache/FRW-ASTRA-WORD228-BOUND-FRAME-DATA-SOURCE-20261117/profile-pin-r1/frame/ROOT-228-SOURCE-ACCEPTANCE.json', 'sha256': '304d9605089cbb8effa15a4e6f9ef216681de7c81545be96bcc65760e440c829'}


COUNTS = {'base': 17730, 'layers': 228, 'native': 17895, 'plugins': 52, 'project': 537}


SOURCE_COMMIT = '889f5f77b424ae956c6f0f4ada722652b8caa733'


EXECUTION_COMMIT = '7964a632da314785c41c0fda4b0b5648cc375f68'


RECEIPT_SHA = '07bd8594911397405c5b222e2421cab2b0ad07e733f016877eb4e9f77655c0c9'


INPUT_SHA = '84e08ba475aac9dffdb89bff88a9e34ffb5c78791cc1d0264d20c93e234df34e'


CANONICAL_REFS = {'input': {'bytes': 76505, 'path': '/home/jericho/.cache/FRW-ASTRA-WORD228-ROOT-INTEGRATION-20261117/root-inputs-source/INPUT-WORD228.private.SOURCE-ONLY.json', 'sha256': '84e08ba475aac9dffdb89bff88a9e34ffb5c78791cc1d0264d20c93e234df34e'}, 'marker': {'bytes': 29550, 'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/FRIDAY-INSTALL.json', 'sha256': '5bbb995ae2074c006c1be0c6cc369d41b36425ed7a49b1d8bcdf92dff067585b'}, 'receipt': {'bytes': 3469299, 'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent.source.json', 'sha256': '07bd8594911397405c5b222e2421cab2b0ad07e733f016877eb4e9f77655c0c9'}, 'stamp': {'bytes': 66779, 'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent/install-stamp.json', 'sha256': '5a4502a4e90623a7befe38c2933c0ceaab0ac8ff57a15c5af3860a740517e2a2'}}


CANONICAL_PINS = {'input': ('84e08ba475aac9dffdb89bff88a9e34ffb5c78791cc1d0264d20c93e234df34e', 76505), 'marker': ('5bbb995ae2074c006c1be0c6cc369d41b36425ed7a49b1d8bcdf92dff067585b', 29550), 'receipt': ('07bd8594911397405c5b222e2421cab2b0ad07e733f016877eb4e9f77655c0c9', 3469299), 'stamp': ('5a4502a4e90623a7befe38c2933c0ceaab0ac8ff57a15c5af3860a740517e2a2', 66779)}


NATIVE_TWO = {'hermes_cli/friday_workspace_word_conversion.py': {'bytes': 11498, 'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent/hermes_cli/friday_workspace_word_conversion.py', 'sha256': 'd9de55e7ec7da21c7c56db8460c38d0696ad3a69986cc0906647f37e10015e11'}, 'tools/scoped_word_conversion.py': {'bytes': 131713, 'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent/tools/scoped_word_conversion.py', 'sha256': '6dd133c4d9572eec1c3e0e24bd025092ab21f1466cbab48bc33d9f3dbed7e910'}}


RETAINED226_DEPENDENCIES = {'hermes_cli/friday_workspace_docx.py': {'sha256': '0bc25b322c58c6a1aba5b4db2b6cf108b0b815b886d2e33f3c9cd2d02e881377', 'bytes': 38137}, 'tools/file_tools.py': {'sha256': 'cf72649df9e5144edcacc94f92dde6bdf5cbd10054ef795755822944889d1bb1', 'bytes': 191360}, 'tools/scoped_word_profiles.py': {'sha256': '4718c402bff018cb23544cc7d207755151c9ad93c327646ac1a84db90c34cf68', 'bytes': 25594}, 'tools/scoped_word_stories.py': {'sha256': 'cf9760ecf984f5477047ad332832bd33a1b85be07c8e9ceca3a861a0ac43dc8f', 'bytes': 14016}}


RETAINED227_DEPENDENCIES = {'tools/scoped_communication.py': {'bytes': 35712, 'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent/tools/scoped_communication.py', 'sha256': 'bdba918298bd5f187bc18f5baa887ef1bb07736a7f4887dae39b77dee35df73f'}, 'tools/session_search_tool.py': {'bytes': 58801, 'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent/tools/session_search_tool.py', 'sha256': '02222a579d9e03cf3970628e2d8f42f4e3d1fe19718da9982b5ef60eb10d4e13'}}


LEAF_PINS = {'agent/web_call_context.py': '83481eaf08254db6dc742419d0615b40c3a1711a8167b0d3c63a67c7d6826042', 'hermes_cli/friday_product_access.py': 'afd6fe8fd51a170887977286b9ef7a92a7aa76286b817b7a56075069ddab3582', 'hermes_cli/friday_user_scope.py': 'abad3f299d1099914455781176ac0a3e09b4d40d4a2afd14b342dcb990087dba', 'hermes_cli/friday_workspace_docx.py': '0bc25b322c58c6a1aba5b4db2b6cf108b0b815b886d2e33f3c9cd2d02e881377', 'hermes_cli/friday_workspace_revision.py': 'a84959c7ddc6fec3a028e5b67b4af64b7ee5d7f462776b9a59150a1891b10dc4', 'hermes_cli/friday_workspace_word_conversion.py': 'd9de55e7ec7da21c7c56db8460c38d0696ad3a69986cc0906647f37e10015e11', 'hermes_cli/plugins_state.py': 'a1a509fc2b8dc8e4082837f303d754c9dc62ba450f980b3281af946822923b4d', 'tools/binary_extensions.py': 'dce64d721d3541194d967f4b1edc9c4ae97e8e30fc64df20d606365ab70132de', 'tools/file_tools.py': 'cf72649df9e5144edcacc94f92dde6bdf5cbd10054ef795755822944889d1bb1', 'tools/file_tools_paths.py': '50fe4d04a31c3b0377b422ef394d6ccdf1bc1b75ac61bdc6962e0ad802397f69', 'tools/file_tools_write_guards.py': '81df0dd7e0415a3c95870ce0935c132a6535e4be2ca44d3001638a0a1dcfad2c', 'tools/read_extract.py': '8f3ad405263470eac948a9f14fa6c0af18144697cf5244c6c8c8a4f7d543b339', 'tools/scoped_communication.py': 'bdba918298bd5f187bc18f5baa887ef1bb07736a7f4887dae39b77dee35df73f', 'tools/scoped_word_conversion.py': '6dd133c4d9572eec1c3e0e24bd025092ab21f1466cbab48bc33d9f3dbed7e910', 'tools/scoped_word_located.py': '4daa683e0a85a15f349d6a6e9b7940cff9761bbc20a003c6aed8fa9f6b2285db', 'tools/scoped_word_profiles.py': '4718c402bff018cb23544cc7d207755151c9ad93c327646ac1a84db90c34cf68', 'tools/scoped_word_stories.py': 'cf9760ecf984f5477047ad332832bd33a1b85be07c8e9ceca3a861a0ac43dc8f', 'tools/scoped_zip.py': 'fdb74316af13069b30acab144dd2d846a7643e7941acc157cfc6ba0b4ddfc127', 'tools/session_search_tool.py': '02222a579d9e03cf3970628e2d8f42f4e3d1fe19718da9982b5ef60eb10d4e13'}


METADATA_BASIS = {'Root_authenticated_closure': {'bytes': 5428, 'path': '/home/jericho/.cache/FRW-ASTRA-WORD228-ROOT-INTEGRATION-20261117/ROOT-INSTALLED228-CLOSED-STATE.json', 'sha256': 'c0ba8d4f714dc34ebaac3595aa7d90401fb4b5f34d6ce88750c231ffe69b6029'}, 'Source_eight_capture': {'old227_eight_not_relabelled': True, 'qualification': 'NOT_RUN_SEPARATE_LIFECYCLE', 'state': 'NOT_CAPTURED_SEPARATE_NOT_ORDINARY_INSTALL_PREREQUISITE'}, 'at_moscow': '2026-11-17T03:33:05.390782+03:00', 'canonical': {'input': {'bytes': 76505, 'path': '/home/jericho/.cache/FRW-ASTRA-WORD228-ROOT-INTEGRATION-20261117/root-inputs-source/INPUT-WORD228.private.SOURCE-ONLY.json', 'sha256': '84e08ba475aac9dffdb89bff88a9e34ffb5c78791cc1d0264d20c93e234df34e'}, 'marker': {'bytes': 29550, 'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/FRIDAY-INSTALL.json', 'sha256': '5bbb995ae2074c006c1be0c6cc369d41b36425ed7a49b1d8bcdf92dff067585b'}, 'receipt': {'bytes': 3469299, 'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent.source.json', 'sha256': '07bd8594911397405c5b222e2421cab2b0ad07e733f016877eb4e9f77655c0c9'}, 'stamp': {'bytes': 66779, 'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent/install-stamp.json', 'sha256': '5a4502a4e90623a7befe38c2933c0ceaab0ac8ff57a15c5af3860a740517e2a2'}}, 'counts': {'base': 17730, 'layers': 228, 'native': 17895, 'plugins': 52, 'project': 537}, 'current_admission': False, 'dated_normal_services_infinity': True, 'default_same_transaction_postconsumer_returncode': 0, 'event_or_read_capability': False, 'execution_commit': '7964a632da314785c41c0fda4b0b5648cc375f68', 'execution_grant': False, 'fresh_default_spec_inspect': True, 'full_native_readback': True, 'future_user_semantics': False, 'native_delta': {'CAS': 8, 'added': 0, 'modified': 2, 'retained': 17893}, 'native_two': {'hermes_cli/friday_workspace_word_conversion.py': {'bytes': 11498, 'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent/hermes_cli/friday_workspace_word_conversion.py', 'sha256': 'd9de55e7ec7da21c7c56db8460c38d0696ad3a69986cc0906647f37e10015e11'}, 'tools/scoped_word_conversion.py': {'bytes': 131713, 'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent/tools/scoped_word_conversion.py', 'sha256': '6dd133c4d9572eec1c3e0e24bd025092ab21f1466cbab48bc33d9f3dbed7e910'}}, 'poststart_optional_Source_custody': {'capture_deadline_monotonic': 291383.458875486, 'completed_stages': [], 'error_class': 'FileNotFoundError', 'failed_stage': 'prepare_normal_gateway_source_custody', 'original_operation_deadline_monotonic': 293972.970598987, 'preserved_service_reserve_seconds': 435, 'qualification': 'NOT_RUN_SEPARATE_LIFECYCLE', 'required_for_ordinary_install': False, 'state': 'UNAVAILABLE_CAPTURE_ONLY_NO_QUALIFICATION'}, 'product_source_commit': '889f5f77b424ae956c6f0f4ada722652b8caa733', 'publisher_returncode': 0, 'schema': 'frw.Root.actual228.readonly-installation-metadata-basis.v1', 'scope': 'Exact datedRoot228 install metadata only. General permission/service/current/rights guards retained. No H/rawclosure/Root8/userdata dereference for peer. Actualcanonical/current observations and every live admission boundary remain Root-only.', 'source_acceptance': {'bytes': 5903, 'path': '/home/jericho/.cache/FRW-ASTRA-WORD228-BOUND-FRAME-DATA-SOURCE-20261117/profile-pin-r1/frame/ROOT-228-SOURCE-ACCEPTANCE.json', 'sha256': '304d9605089cbb8effa15a4e6f9ef216681de7c81545be96bcc65760e440c829'}, 'state': 'DATED_CLOSED228_SOURCE_METADATA_ONLY'}


def require_source_bound():
    if SOURCE_BOUND is not True:
        raise ValueError('DOCX226_SOURCE_UNBOUND_BEFORE_ROOT_RUNTIME_IO')


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
    if not SOURCE_BOUND and (p.is_relative_to(H) or p.is_relative_to(STATE) or p==SLOT or p.is_relative_to(Path('/proc'))):
        require_source_bound()
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
    require_source_bound()
    configs={}
    for label,limit in PROFILE_CONFIG_LIMITS.items():
        path=DATABASES[label].parent/'config.yaml'
        raw=_read_bounded(path,limit,False)
        configs[label]=dict(path=str(canonical_path(path)),bytes=len(raw),sha256=digest(raw))
    return configs


def module(reference):
    need(reference_shape(reference),'DOCX226_PARENT_SOURCE_BINDING_UNBOUND')
    raw=read_reference(reference)
    value=types.ModuleType('_word_pinned_'+reference['sha256'][:12]); value.__file__=reference['path']
    exec(compile(raw,reference['path'],'exec'),value.__dict__); return value


def process_bytes(pid,name):
    require_source_bound()
    need(type(pid) is int and pid>0 and name in ('stat','cgroup','environ','cmdline'),'F07_BOUNDED_PROCESS_METADATA_ONLY')
    with (Path('/proc')/str(pid)/name).open('rb') as f: raw=f.read(DEFAULT_LIMIT+1)
    need(len(raw)<=DEFAULT_LIMIT,'F07_PROCESS_METADATA_OVERSIZE'); return raw


def kernel(pid):
    require_source_bound()
    ticks=int(process_bytes(pid,'stat').rsplit(b')',1)[1].split()[19])
    return dict(pid=pid,start_time=ticks,boot_id=read_kernel_boot())


def read_kernel_boot():
    require_source_bound()
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def services(environment_basis):
    require_source_bound()
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
        need(env.get('HERMES_HOME')==str(H) and all(type(v) is str for v in env.values()),
             'DOCX226_FRESH_PER_SERVICE_PRODUCT_HOME_REQUIRED')
        if environment_basis is not None:
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
    require_source_bound()
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
    require_source_bound()
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
    require_source_bound()
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
    require_source_bound()
    rows={}
    for name in ('agent.log','gateway.log'):
        path=H/'profiles/telegram-bot-8812646969/logs'/name
        need(not any(p.is_symlink() for p in (path,*path.parents)),'F07_LOG_LINK')
        s=path.stat(); need(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and not stat.S_IMODE(s.st_mode)&0o002,'F07_LOG_CUSTODY_UNSAFE')
        rows[str(path)]=list(identity(s))
    return dict(schema='frw.Root.DOCX226.technical-log-metadata-cursor.v1',files=rows,contents_read=False)


def stable_native(native):
    result=clone(native); result.get('global_work',{}).pop('observed_monotonic',None); return result


def validate_native_permission_source(name, location, sha256):
    """Pure exact native permission Code metadata, never an import or access grant."""
    need(name in ('hermes_cli/friday_user_scope.py','hermes_cli/friday_product_access.py','hermes_cli/plugins_state.py')
         and canonical_path(location)==H/'hermes-agent'/name and sha256==LEAF_PINS[name],
         'DOCX226_EXACT_NATIVE_PERMISSION_SOURCE_REQUIRED')
    return True


def validate_permission_namespace(bindings, accounts, row):
    """Pure policy namespace checks; no read_file or history API is granted here."""
    need(type(bindings) is list and len(bindings)==1 and type(bindings[0]) is dict
         and bindings[0].get('runtime_profile')==PRINCIPAL['profile_name'],
         'DOCX226_NATIVE_PRINCIPAL_PROFILE_NOT_CURRENT')
    need(type(accounts) is list and len(accounts)==1 and type(accounts[0]) is dict
         and type(accounts[0].get('runtime_profiles')) is list
         and PRINCIPAL['profile_name'] in accounts[0]['runtime_profiles']
         and type(row) is dict and row.get('enabled') is True
         and type(row.get('generation')) is int and row['generation']>=1,
         'DOCX226_CURRENT_NATIVE_ACCESS_DISABLED_OR_CHANGED')
    return True


def permission_current():
    """Future Root only: current native principal/policy namespace qualification.

    PluginState ctor only binds names; directory_storage_readonly and
    get_storage_readonly use the existing repair=False API. No data_dir, writer,
    provisioning, token read, model call or user-supplied source is invoked.
    """
    require_source_bound()
    need(sys.dont_write_bytecode is True,'DOCX226_NATIVE_IMPORT_REQUIRES_B_MODE')
    native=H/'hermes-agent'
    need(NATIVE_PYTHON!='UNBOUND_ROOT_NATIVE226_INTERPRETER'
         and canonical_path(NATIVE_PYTHON)==Path(sys.executable),
         'DOCX226_ROOT_NATIVE226_INTERPRETER_UNBOUND_OR_CHANGED')
    site=(canonical_path(NATIVE_PYTHON).parent.parent/'lib')/('python'+str(sys.version_info.major)+'.'+str(sys.version_info.minor))/'site-packages'
    # Use the existing installed native consumer interpreter; globalvenv lacks ruamel. -I/-S are retained;
    # append its explicit package directory without executing .pth/site hooks.
    for path in (native,site):
        need(not any(p.is_symlink() for p in (path,*path.parents)) and path.is_dir(),
             'DOCX226_EXPLICIT_NATIVE_IMPORT_ROOT_REQUIRED')
    previous=list(sys.path)
    try:
        sys.path[:0]=[str(native),str(site)]
        scope=importlib.import_module('hermes_cli.friday_user_scope')
        access=importlib.import_module('hermes_cli.friday_product_access')
        statecode=importlib.import_module('hermes_cli.plugins_state')
        for code,name in ((scope,'hermes_cli/friday_user_scope.py'),(access,'hermes_cli/friday_product_access.py'),
                          (statecode,'hermes_cli/plugins_state.py')):
            validate_native_permission_source(name,str(code.__file__),digest(read(code.__file__,private=False)))
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
        accounts=[] if policy is None else [r for r in policy['accounts'] if
            (r['platform'],r['transport_profile'],r['account_id'])==('telegram',PRINCIPAL['transport_profile'],'8751854128')]
        row=admitted['users'].get(key)
        validate_permission_namespace(bindings,accounts,row)
        proposed=scope.UserScope(H,home,PRINCIPAL['profile_name'],('telegram',PRINCIPAL['transport_profile'],'8751854128',PRINCIPAL['user_id']),
                            clone(bindings[0]),(home_info.st_dev,home_info.st_ino),row['generation'])
        # A local proposed object qualifies current policy/home only. It is never
        # installed into _CURRENT/_SOURCE or attached to a TG event/agent.
        with scope.authority(home):proposed.check()
        marker=ref(home/scope.MARKER)
        with scope.authority(H):
            need(scope.policy(H)==isolation and access.access_policy()==policy
                 and access.current_access(state)==admitted and state.directory_storage_readonly==directory,
                 'DOCX226_NATIVE_PERMISSION_SEMANTIC_CAS_CHANGED')
        need(profile_config_refs()==before and identity(home.stat())==identity(home_info)
             and identity(statepath.stat())==identity(state_info),'DOCX226_NATIVE_PERMISSION_FILE_CAS_CHANGED')
        return dict(schema='frw.Root.DOCX226.native-context-policy-namespace.v1',
            state='PREFLIGHT_POLICY_NAMESPACE_ONLY_NOT_NATIVE_EVENT_AUTHORITY',
            planned_principal_only=True,new_Telegram_event_capability_issued=False,principal_key=key,
            runtime_profile=PRINCIPAL['profile_name'],admission_generation=row['generation'],
            binding_sha256=digest(encoded(bindings[0])),access_policy_sha256=digest(encoded(policy)),
            access_document_sha256=digest(encoded(admitted)),state_identity=list(identity(state_info)),
            home_identity=list(identity(home_info)),scope_marker=marker,profile_configs=before,
            native_capability_check=True,file_read_permission_required=False,write_file_required=False,readonly=True,
            history_access_granted_by_this_check=False,context_history_policy='ROOT_EXPLICIT_CURRENT_DECISION_REQUIRED')
    finally:
        sys.path[:]=previous


def fresh(proof,*,wall=None,mono=None):
    wall=time.time() if wall is None else wall; mono=time.monotonic() if mono is None else mono
    need(all(type(proof.get(k)) in (int,float) and math.isfinite(proof[k]) for k in ('created_at','expires_at','created_monotonic','expires_monotonic')),'F07_FINITE_PROOF_CLOCK_REQUIRED')
    need(0<=proof['created_at']<=wall<proof['expires_at']<=proof['created_at']+120
         and 0<=proof['created_monotonic']<=mono<proof['expires_monotonic']<=proof['created_monotonic']+120,'F07_EXPIRED_OR_FUTURE_PROOF')
    return min(proof['expires_monotonic'],mono+proof['expires_at']-wall)


def lock_held(path,owner):
    require_source_bound()
    need(type(owner) is dict and set(owner)=={'pid','start_time','boot_id'} and kernel(owner['pid'])==owner,'F07_LOCK_OWNER_CHANGED')
    p=canonical_path(path); s=p.stat()
    need(not any(q.is_symlink() for q in (p,*p.parents)) and stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600,'F07_LOCK_CUSTODY_CHANGED')
    device=f'{os.major(s.st_dev):02x}:{os.minor(s.st_dev):02x}:{s.st_ino}'
    need(any(len(v:=row.split())>=6 and v[1]=='FLOCK' and v[3]=='WRITE' and v[4]==str(owner['pid']) and v[5]==device for row in Path('/proc/locks').read_text().splitlines()),'F07_EXCLUSIVE_NAMED_LOCK_NOT_HELD')


def installation_metadata(closure):
    """Pure exact Root-normalized fixed228 Source metadata; no reference is read.

    The caller must authenticate CLOSURE by its exact reference. This dated
    metadata never supplies fresh current admission, access or user semantics.
    """
    need(type(closure) is dict
         and closure.get('schema')=='frw.Root.actual228.readonly-installation-metadata-basis.v1'
         and closure.get('state')=='DATED_CLOSED228_SOURCE_METADATA_ONLY'
         and closure.get('product_source_commit')==SOURCE_COMMIT
         and closure.get('execution_commit')==EXECUTION_COMMIT
         and encoded(closure.get('counts'))==encoded(COUNTS)
         and encoded(closure.get('native_delta'))==encoded(dict(modified=2,added=0,CAS=8,retained=17893)),
         'DOCX228_ACTUAL_NORMALIZED_INSTALLATION_METADATA_REQUIRED')
    canonical=closure.get('canonical')
    need(type(canonical) is dict and set(canonical)==set(CANONICAL_PINS),
         'DOCX228_CANONICAL4_METADATA_REQUIRED')
    for name,(want,size) in CANONICAL_PINS.items():
        row=canonical[name]
        need(reference_shape(row) and row['sha256']==want and row['bytes']==size
             and row['path']==CANONICAL_REFS[name]['path'],
             'DOCX228_CANONICAL_METADATA_TUPLE_CHANGED')
    need(encoded(canonical)==encoded(CANONICAL_REFS),
         'DOCX228_EXACT_CANONICAL4_METADATA_PATHS_REQUIRED')
    need(encoded(closure.get('source_acceptance'))==encoded(ACCEPTANCE),
         'DOCX228_INSTALLATION_SOURCE_ACCEPTANCE_METADATA_CHANGED')
    rows=closure.get('native_two')
    need(type(rows) is dict and set(rows)==set(NATIVE_TWO)
         and all(reference_shape(row) for row in rows.values())
         and encoded(rows)==encoded(NATIVE_TWO),
         'DOCX228_NATIVE_TWO_METADATA_CHANGED')
    need(closure.get('publisher_returncode')==0
         and type(closure.get('publisher_returncode')) is int
         and closure.get('default_same_transaction_postconsumer_returncode')==0
         and type(closure.get('default_same_transaction_postconsumer_returncode')) is int
         and all(closure.get(k) is True for k in
                 ('full_native_readback','fresh_default_spec_inspect','dated_normal_services_infinity'))
         and all(closure.get(k) is False for k in
                 ('current_admission','execution_grant','event_or_read_capability','future_user_semantics')),
         'DOCX228_DATED_CLOSURE_NOT_CURRENT_AUTHORITY_REQUIRED')
    # Strict by-value binding also preserves the original unavailable optional
    # capture and its lack of ordinary-install/READ prerequisite or qualification.
    # No raw closure, Source-eight capture or custody reference is dereferenced.
    need(encoded(closure)==encoded(METADATA_BASIS),
         'DOCX228_EXACT_ROOT_NORMALIZED_BASIS_CHANGED')
    return dict(schema='frw.Root.fixed228.installation-source-basis.v1',
                state='DATED_CLOSED228_METADATA_ONLY',counts=clone(COUNTS),
                product_source_commit=SOURCE_COMMIT,
                canonical4={('source_receipt' if k=='receipt' else k):clone(v)
                            for k,v in canonical.items()},
                native_two=clone(rows),native_delta=clone(closure['native_delta']),
                retained_dependency_four=clone(RETAINED226_DEPENDENCIES),
                retained_dependency_four_scope='UNCHANGED_226_DEPENDENCIES_NOT_228_INSTALL_TARGETS',
                retained_dependency_two=clone(RETAINED227_DEPENDENCIES),
                retained_dependency_two_scope='UNCHANGED_227_DEPENDENCIES_NOT_228_INSTALL_TARGETS',
                Source_eight_capture=clone(closure['Source_eight_capture']),
                poststart_optional_Source_custody=clone(closure['poststart_optional_Source_custody']),
                current_admission=False,user_semantic_acceptance=False,
                dated_services_never_future_admission=True,canonical_values_assessed=False)


def installation_shapes(closure,receipt,marker,stamp,inputs):
    """Pure check of genuine future canonical values; never manufactures them."""
    metadata=installation_metadata(closure)
    need(type(receipt) is dict and type(marker) is dict and type(stamp) is dict and type(inputs) is dict,
         'DOCX228_ACTUAL_CANONICAL_VALUES_REQUIRED')
    need((len(receipt.get('layers',[])),len(receipt.get('files',{})),receipt.get('source_file_count'),
          len(marker.get('plugin_files',{})),len(inputs.get('project_files',{})))
         ==(228,17895,17730,52,537)
         and marker.get('source_receipt_sha256')==RECEIPT_SHA and marker.get('input_sha256')==INPUT_SHA
         and type(stamp.get('fridaySource')) is dict
         and stamp['fridaySource'].get('layers')==receipt['layers']
         and stamp['fridaySource'].get('baseTree')==receipt.get('base_tree'),
         'DOCX228_CANONICAL_TUPLE_CHANGED')
    for name,want in LEAF_PINS.items():
        need(receipt.get('files',{}).get(name,{}).get('sha256')==want,
             'DOCX228_ACCEPTED_NATIVE_DEPENDENCY_CHANGED')
    # CLOSED228 deliberately contains no fresh runtime environment assertion.
    return metadata


def check(proof_ref,*,run_id,scenario,stage):
    """Deliberately not an ordinary pre-intent/admission checker."""
    raise ValueError('FIXED227_METADATA_ONLY_NO_ADMISSION_ENTRYPOINT')


def installation(effect):
    raise ValueError('FIXED227_METADATA_ONLY_USE_EXPLICIT_CANONICAL_CHECKS')


def observe(effect,*,stage='BASELINE'):
    raise ValueError('FIXED227_METADATA_ONLY_NO_CURRENT_OBSERVATION_ENTRYPOINT')


def observe_readonly(*,phase,run_id,closure_ref,acceptance_ref,resource_limits):
    raise ValueError('FIXED227_METADATA_ONLY_NO_CURRENT_OBSERVATION_ENTRYPOINT')


if __name__=='__main__':
    raise SystemExit('REFUSED: fixed228 metadata-only Source library; no admission or operation')
