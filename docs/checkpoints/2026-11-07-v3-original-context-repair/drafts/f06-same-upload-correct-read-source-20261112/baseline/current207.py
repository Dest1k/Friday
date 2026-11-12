"""Root-only F06 first ordinary wrong-read prerequisite; import is inert.

SOURCE ONLY: unbound_proof() grants nothing. Only future Root check/observe calls
read installed metadata, source hashes, canonical tester JSON or retained input.
No Store, native message body, token, document application, model or writer API.
The unchanged gate202 transport supplies fresh same-B readonly observations;
its old check() and current203 observe/check are never called.
"""
import contextlib
import datetime as dt
import hashlib
import json
import math
import os
import re
import sqlite3
import stat
import subprocess
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
H = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
STATE = Path('/home/jericho/.local/share/friday-telegram-bot-test')
G = Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE-F01-BOUND-TESTER-PREP-20261111/gate202.py')
G_SHA = '52c27671815632cf4fa884ee187a74fad2671e1fd53003a2d0512083bcef8c9a'
CLOSURE = Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/CORE207-ACTUAL-INSTALLED-CLOSED-20261112.json')
CLOSURE_SHA = '996b43c584c8eb6d5c8dbbeb60f500958c873427cda0881ae74a7618d920f963'
RECEIPT = 'faf5d6ad698b7250b09545508352c120c0c8cdf653cecb9c37afeb2601c98a4b'
INPUT = 'c7a01f639606652f75db11418b5abd6e3a03b0babea09627570e39b0865ff838'
EXPECTED = dict(source_layers=207, project_files=495, native_files=17891,
                plugin_files=52, base_source_files=17730,
                source_receipt_sha256=RECEIPT, input_sha256=INPUT)
SID = '20261030_093055_43bba39f'
KEY = 'agent:telegram-bot-8812646969:telegram:dm:8812646969'
SLOT = Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
DATABASES = {'default': H/'state.db', 'dest': H/'profiles/dest_telegram/state.db',
             'tester': H/'profiles/telegram-bot-8812646969/state.db'}
SESSION_FIELDS = ('id', 'source', 'user_id', 'chat_id', 'chat_type', 'session_key', 'profile_name', 'transport_profile')
MESSAGE_METADATA = ('id', 'session_id', 'role', 'timestamp', 'platform_message_id', 'active', 'compacted')
# These are exact207 source bytes, not a substitute for the separate genuine
# installed runtime privacy-consumer observation Root must accept before dispatch.
RUNTIME_HASHES = {
 'agent/agent_runtime_helpers.py':'b3a71476ab48aecb4b4fe7058c2a7626c769b01a919c50c9f5935e96b67da39e',
 'agent/display.py':'9e0b8e2721260f513031194b04e86da3c57c118b3543850abe3658cf00126aec',
 'agent/message_sanitization.py':'08823b1e54f6aa78f49ebf1f0f92092f9c558bd982c3961ef9ed8cd99642f5ec',
 'agent/session_persistence.py':'de1049ed9adc152c38349e6942edf79f3ef1778e2353a9dc3a68f793716e5006',
 'hermes_cli/friday_prompt_scope.py':'c51ac7998ec909a67283fb0d164cac91ea3f28a7e819600c025d03ad3488d450',
 'hermes_cli/friday_workspace_ooxml_password.py':'0be85ff3458cd47ffd9818a4f4791b0b9f67bfd4131e6fe9b688c23fe4619d86',
 'hermes_state_messages.py':'a4ae3e55ffe47bc2029e816bd52c77f075319d0fd2eb05714fcdfc7b3dd0f529',
 'tools/file_tools.py':'b834615c95438c2f1cb725247cc2ea0b6e1d5e1566cc3498fec2a069bc21a40f',
 'tools/scoped_odf_password.py':'b66d95d1f2a4223ffcc9d54e28d13976b49e5e2f041e1c12456a8c7b85922d9d',
 'tools/scoped_ooxml_password.py':'59c65471582a30baf61ed8367925b477d00af70d6d1211e6044ecb2a3d35029c',
 'tools/scoped_ooxml_password_edit.py':'e5c9588cd5e22590809cb1231affa72238435c98c43429041d6b37c5761f3ca4',
 'gateway/ordinary_turn_projection.py':'3a6b003622bc17ff5265e5c5117e0eb1f4572676d967763cb368e80947fc79b4'}
SCHEMA = 'frw.Root.F06.current207-preintent.v1'
PROOF_FIELDS = {'schema','status','operator','created_at','expires_at','created_monotonic',
 'expires_monotonic','boot_id','contract_effect','whole_effect_sha256',
 'installation_acceptance','installation_closure','runtime_privacy_review',
 'history_semantic_review','observed','shared_slot_owner'}
LIMIT = 'ALL_PROFILE_IN_MEMORY_PENDING_QUEUES_APPROVALS_NOT_EXPOSED'


def require(ok, why):
    if not ok:
        raise ValueError(why)


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False)+'\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'F06 duplicate JSON key')
        result[key] = value
    return result


def sha(value):
    return type(value) is str and re.fullmatch('[a-f0-9]{64}', value) is not None


def identity(s):
    return dict(device=s.st_dev, inode=s.st_ino, uid=s.st_uid, gid=s.st_gid,
                mode=stat.S_IMODE(s.st_mode), nlink=s.st_nlink, bytes=s.st_size,
                mtime_ns=s.st_mtime_ns, ctime_ns=s.st_ctime_ns)


def canonical_path(path):
    text=path if type(path) is str else str(path) if isinstance(path,Path) else None
    require(type(text) is str and text.startswith('/') and not text.startswith('//')
          and not any(ord(ch)<32 or 127<=ord(ch)<=159 for ch in text), 'F06_CANONICAL_ABSOLUTE_PATH_REQUIRED')
    try:text.encode('utf-8')
    except UnicodeError:raise ValueError('F06_CANONICAL_UTF8_PATH_REQUIRED') from None
    require((text=='/' or not any(part in ('','.','..') for part in text.split('/')[1:]))
          and str(Path(text))==text, 'F06_LEXICAL_PATH_ALIAS_REFUSED')
    return Path(text)

def safe_path(path):
    p = canonical_path(path)
    require(not any(q.is_symlink() for q in (p,*p.parents)),
            'F06 absolute no-symlink current path required')
    return p


def read(path, limit=24*1024**2, private=False):
    p = safe_path(path)
    with os.fdopen(os.open(p, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK), 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid()
                and before.st_nlink==1 and not stat.S_IMODE(before.st_mode)&0o002
                and (not private or stat.S_IMODE(before.st_mode)==0o600),
                'F06 unsafe owned current file')
        raw = stream.read(limit+1)
        after = os.fstat(stream.fileno())
    require(len(raw)<=limit and identity(before)==identity(after)==identity(safe_path(p).stat()),
            'F06 current file changed or exceeded bound')
    return raw


def parse(raw):
    return json.loads(raw, object_pairs_hook=unique)


def doc(path, private=False):
    return parse(read(path, private=private))


def ref(path, private=False):
    raw = read(path, private=private)
    return dict(path=str(Path(path)), bytes=len(raw), sha256=digest(raw))


def reference(r, private=True):
    require(type(r) is dict and set(r) in ({'path','sha256'}, {'path','bytes','sha256'})
            and type(r['path']) is str and sha(r['sha256']), 'F06 exact pinned reference required')
    raw = read(r['path'], private=private)
    require(digest(raw)==r['sha256'] and ('bytes' not in r or type(r['bytes']) is int
            and len(raw)==r['bytes']), 'F06 pinned reference drift')
    return raw


def readref(r, private=True):
    return parse(reference(r, private))


def transport():
    raw = read(G)
    require(digest(raw)==G_SHA, 'F06 unchanged native readonly transport source drift')
    module = types.ModuleType('_F06_unchanged_gate202_transport')
    module.__file__ = str(G)
    exec(compile(raw, str(G), 'exec'), module.__dict__)
    return module


def source(effect):
    r = effect.get('adapter', {})
    require(r.get('path')==str(HERE/'f06_source.py'), 'F06 exact local source module required')
    raw = reference(r)
    module = types.ModuleType('_F06_pinned_pure_source')
    module.__file__ = r['path']
    exec(compile(raw, r['path'], 'exec'), module.__dict__)
    return module


def validate_effect(proof):
    effect = proof.get('contract_effect')
    require(type(effect) is dict, 'F06 exact effect body required')
    a = source(effect)
    excluded = {'authority','authority_id','root_current_proof','status'}
    require(set(effect)==a.FIELDS-excluded and digest(encoded(effect))==proof.get('whole_effect_sha256'),
            'F06 whole effect digest mismatch')
    c = a.unbound()
    c.update(effect)
    a.contract_shape(c, bound=False)
    require(a.effect(c)==effect and c['product']==EXPECTED, 'F06 exact actual207 effect required')
    require(type(c['run_id']) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', c['run_id'])
            and c['run_id']!='UNBOUND' and sha(c['scenario_sha256']), 'F06 private run/scenario unbound')
    require(all(a.ref(c[k]) for k in ('scenario_ref','adapter','footer','actual_root_B_checker'))
            and c['actual_root_B_checker']==ref(Path(__file__), private=True), 'F06 immutable source/checker refs required')
    scenario_raw = reference(c['scenario_ref'])
    s = parse(scenario_raw)
    a.scenario_shape(s)
    require(scenario_raw==a.encoded(s) and digest(scenario_raw)==c['scenario_sha256'], 'F06 private scenario drift')
    require(type(c['root_proofs']) is dict and set(c['root_proofs'])==a.PROOFS
            and all(a.ref(r) for r in c['root_proofs'].values()), 'F06 all original Root evidence refs required')
    for r in c['root_proofs'].values():
        reference(r)
    reference(c['footer'])
    b = c['boundary']
    require(type(b) is dict and set(b)==a.BOUNDARY and all(sha(b[k]) for k in a.BOUNDARY-
            {'gateway','B','phase_unconsumed','uploads_this_operation','producer_calls','restarts'})
            and b['phase_unconsumed'] is True
            and all(type(b[k]) is int and b[k]==v for k,v in
                    {'uploads_this_operation':1,'producer_calls':0,'restarts':0}.items()),
            'F06 current once/ingress boundary unbound')
    require(type(b['B']) is dict and b['B'].get('profile')=='telegram-bot-8812646969'
            and b['B'].get('session_id')==SID and b['B'].get('session_key')==KEY
            and type(b['B'].get('native_max_id')) is int and b['B']['native_max_id']>=0,
            'F06 actual same-B principal required')
    r = c['resources']
    require(type(r) is dict and set(r)==set(a.TIMING)|{'cpu_seconds','max_rss_bytes','disk_bytes','clock','owned_parent_wait_cleanup'}
            and all(type(r[k]) is int and r[k]==v for k,v in a.TIMING.items())
            and type(r['cpu_seconds']) is int and r['cpu_seconds']>0
            and type(r['max_rss_bytes']) is int and 0<r['max_rss_bytes']<=2*1024**3
            and type(r['disk_bytes']) is int and 0<r['disk_bytes']<=64*1024**2
            and a.ref(r['clock']) and a.ref(r['owned_parent_wait_cleanup']), 'F06 finite executable consumer resource refs required')
    reference(r['clock']); reference(r['owned_parent_wait_cleanup'])
    return c, s


def fresh(proof, wall=None, mono=None):
    wall = time.time() if wall is None else wall
    mono = time.monotonic() if mono is None else mono
    fields = ('created_at','expires_at','created_monotonic','expires_monotonic')
    require(all(type(proof.get(k)) in (int,float) and math.isfinite(proof[k]) for k in fields),
            'F06 finite Root proof clocks required')
    require(0<=proof['created_at']<=wall<proof['expires_at']<=proof['created_at']+120
            and 0<=proof['created_monotonic']<=mono<proof['expires_monotonic']<=proof['created_monotonic']+120,
            'F06 expired/future Root120 wall or monotonic proof')
    return min(proof['expires_monotonic'], mono+proof['expires_at']-wall)


def validate_proof(proof):
    require(type(proof) is dict and set(proof)==PROOF_FIELDS and proof.get('schema')==SCHEMA
            and proof.get('operator')=='Root' and proof.get('status')=='ROOT_BOUND',
            'F06 genuine Root proof unbound')
    deadline = fresh(proof)
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    require(proof.get('boot_id')==boot, 'F06 Root proof from different boot')
    return deadline


def installation(proof):
    require(proof['installation_closure'].get('path')==str(CLOSURE)
            and proof['installation_closure'].get('sha256')==CLOSURE_SHA, 'F06 accepted exact207 closure pin required')
    closure = readref(proof['installation_closure'])
    require(closure.get('schema')=='friday.root.actual207.complete-closure.v1'
            and closure.get('state')=='INSTALLED207_PROJECT495_NATIVE17891_SERVICES_HEALTHY_OPERATION_CLOSED'
            and closure.get('actors_and_boundary_closed') is True
            and closure.get('full_selected_native_files_readback') is True
            and closure.get('selected_native_file_count')==17891
            and all(closure.get(k)==0 for k in ('publisher_client_code','fresh_DEFAULT_code','complete_root_boundary_code')),
            'F06 actual installed207 accepted closure absent')
    require(proof['installation_acceptance']==closure['source_acceptance'], 'F06 exact207 source acceptance drift')
    readref(proof['installation_acceptance'])
    for key in ('operation','root_return','root_source_decision','canonical_CP207','committed'):
        reference(closure[key])
    installed = closure['installed']
    require({k:installed.get(k) for k in ('layers','project','native','plugins','base')}==
            dict(layers=207,project=495,native=17891,plugins=52,base=17730), 'F06 closure installed tuple mismatch')
    canonical = {k:readref(r, private=False) for k,r in installed['canonical4'].items()}
    receipt,marker,stamp,inputs = (canonical[k] for k in ('source_receipt','marker','stamp','current_input'))
    require(installed['canonical4']['source_receipt']['sha256']==RECEIPT
            and installed['canonical4']['current_input']['sha256']==INPUT
            and marker['source_receipt_sha256']==RECEIPT and marker['input_sha256']==INPUT
            and (len(receipt['layers']),len(receipt['files']),len(marker['plugin_files']),len(inputs['project_files']))==(207,17891,52,495)
            and receipt['source_file_count']==17730 and stamp['fridaySource']['layers']==receipt['layers']
            and stamp['fridaySource']['baseTree']==receipt['base_tree'], 'F06 actual207 receipt/marker/stamp/input drift')
    for name,value in marker['plugin_files'].items():
        require(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts
                and digest(read(H/name))==value, 'F06 installed plugin drift')
    for name,value in RUNTIME_HASHES.items():
        require(digest(read(H/'hermes-agent'/name))==value, 'F06 installed207 privacy/protected helper drift')
    return closure


def service(unit):
    fields = {'LoadState','ActiveState','SubState','MainPID','ControlPID','ControlGroup','InvocationID','UnitFileState','RuntimeMaxUSec','NRestarts'}
    result = subprocess.run(['/usr/bin/systemctl','--user','show',unit,'--property='+','.join(sorted(fields))],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5, check=True)
    require(len(result.stdout)<=65536 and len(result.stderr)<=65536, 'F06 bounded service properties required')
    pairs = [row.split('=',1) for row in result.stdout.decode().splitlines()]
    require(all(len(row)==2 for row in pairs), 'F06 malformed service properties')
    values = unique(pairs)
    require(set(values)==fields and all(values[k]==v for k,v in dict(LoadState='loaded',ActiveState='active',
        SubState='running',ControlPID='0',UnitFileState='enabled',RuntimeMaxUSec='infinity',NRestarts='0').items()),
        'F06 permanent service not healthy')
    kernel = transport().kernel(int(values['MainPID']))
    require('0::'+values['ControlGroup'] in (Path('/proc')/values['MainPID']/'cgroup').read_text().splitlines(),
            'F06 service process cgroup drift')
    return dict(unit=values, identity=kernel)


def gateway():
    raw = read(H/'gateway_state.json')
    state = parse(raw)
    t = state.get('platforms',{}).get('telegram',{})
    require(type(state.get('pid')) is int and type(state.get('start_time')) is int
            and state.get('gateway_state')=='running' and state.get('active_agents')==0
            and state.get('active_work') is None and state.get('restart_requested') is False
            and state.get('session_store',{}).get('status')=='ok'
            and state.get('served_profiles')==['default','dest_telegram','telegram-bot-8812646969']
            and state.get('hermes_home')==str(H) and t.get('state')=='connected'
            and t.get('needs_attention') is False and t.get('writer_pid')==state['pid']
            and t.get('writer_start_time')==state['start_time'], 'F06 current all-profile gateway/writer not quiescent')
    require(state.get('argv')==[str(H/'hermes-agent/hermes_cli/main.py'),'gateway','run'], 'F06 supported gateway source required')
    kernel = transport().kernel(state['pid'])
    require(kernel['start_time']==state['start_time'], 'F06 gateway birth drift')
    environment = read_process(state['pid'],'environ').split(b'\0')
    require(b'HERMES_HOME='+str(H).encode() in environment
            and str(H/'hermes-agent').encode() in read_process(state['pid'],'cmdline'),
            'F06 gateway effective home/source does not match installed207')
    latest = max(max(s.st_mtime_ns,s.st_ctime_ns) for s in
                 (safe_path(H/'hermes-agent'/name).stat() for name in RUNTIME_HASHES))
    born = time.time()-float(Path('/proc/uptime').read_text().split()[0])+state['start_time']/os.sysconf('SC_CLK_TCK')
    require(born*1e9>latest, 'F06 gateway predates current207 privacy/protected helper source')
    return state,raw,kernel


def databases():
    result = {}
    deadline = time.monotonic()+12
    for label,path in DATABASES.items():
        p = safe_path(path)
        before = p.stat()
        require(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1
                and not stat.S_IMODE(before.st_mode)&0o002, 'F06 current3DB custody unsafe')
        stable = {k:identity(before)[k] for k in ('device','inode','uid','gid','mode','nlink')}
        with contextlib.closing(sqlite3.connect(p.as_uri()+'?mode=ro',uri=True,timeout=1)) as db:
            db.set_progress_handler(lambda:int(time.monotonic()>=deadline),1000)
            db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
            count,maximum = db.execute('SELECT count(*),max(id) FROM messages').fetchone()
            require(type(count) is int and 0<=count<=100000, 'F06 bounded metadata inventory exceeded')
            leases = db.execute('SELECT count(*) FROM session_turn_leases').fetchone()[0]
            pending = db.execute("SELECT count(*) FROM async_delegations WHERE state IN ('running','stalling','finalizing') OR delivery_state IN ('pending','claimed','deferred')").fetchone()[0]
            sessions = db.execute('SELECT '+','.join(SESSION_FIELDS)+' FROM sessions ORDER BY id').fetchall()
            rows = db.execute('SELECT '+','.join(MESSAGE_METADATA)+' FROM messages ORDER BY id').fetchall()
            db.rollback()
        require(leases==pending==0 and len(sessions)<=10000 and len(rows)==count,
                'F06 all-origin active lease/delegation or unbounded metadata')
        require({k:identity(p.stat())[k] for k in stable}==stable, 'F06 current3DB identity drift')
        spool = safe_path(p.parent/'pending_messages')
        require(not spool.exists() or spool.is_dir() and not list(spool.iterdir()), 'F06 pending ingress spool present')
        value = dict(path=str(p),identity=stable,messages=count,max_message_id=maximum,sessions=len(sessions),
            leases=leases,all_origin_pending_delegations=pending,session_metadata_sha256=digest(encoded(sessions)),
            message_metadata_sha256=digest(encoded(rows)),pending_message_entries=0)
        if label=='tester':
            found = [dict(zip(SESSION_FIELDS,row)) for row in sessions if row[0]==SID]
            expected = dict(id=SID,source='telegram',user_id='8812646969',chat_id='8812646969',chat_type='dm',
                            session_key=KEY,profile_name='telegram-bot-8812646969',transport_profile='default')
            require(found==[expected], 'F06 current native authorization/principal drift')
            value['principal'] = expected
        result[label] = value
    return result


def pristine(row,c,s,raw,now):
    fields = {'id','scenario','scenario_sha256','created_at','deadline','step','status','send_state','sent_ids',
              'seen','message_ids','observations','update_count','last_text','repeat_count','send_attempts','capture_start_offset'}
    require(set(row)==fields and row['id']==c['run_id'] and row['scenario']==s
            and row['scenario_sha256']==c['scenario_sha256'] and raw==encoded(row)
            and row['status']=='PREPARED' and row['send_state']=='none'
            and all(type(row[k]) is int and row[k]==0 for k in ('step','update_count','repeat_count','send_attempts'))
            and all(type(row[k]) is list and row[k]==[] for k in ('sent_ids','seen','message_ids','observations'))
            and row['last_text'] is None and type(row['capture_start_offset']) is int and row['capture_start_offset']>=0
            and type(row['deadline']) in (int,float) and math.isfinite(row['deadline']), 'F06 own row not exact pristine ordinary run')
    created = dt.datetime.fromisoformat(row['created_at']).timestamp()
    require(created<=now<row['deadline']<=created+301, 'F06 own pristine run expired or clock extended')


def history(c,s):
    root = safe_path(STATE/'runs')
    paths = sorted(root.iterdir())
    require(len(paths)<=1025 and all(p.suffix=='.json' and p.is_file() for p in paths), 'F06 bounded canonical history required')
    records,ids = [],[]
    total = 0
    for path in paths:
        raw = read(path,limit=1024**2,private=True); total += len(raw)
        require(total<=16*1024**2, 'F06 canonical history aggregate bound exceeded')
        row = parse(raw)
        require(row.get('id')==path.stem and raw==encoded(row), 'F06 canonical run identity/encoding drift')
        if row['id']==c['run_id']:
            pristine(row,c,s,raw,time.time())
            continue
        # Exact/source equivalents are refused mechanically. Semantically changed
        # captions, compacted/unlogged effects still require independent Root review.
        for step in row.get('scenario',{}).get('steps',[]):
            require(step.get('input',{}).get('sha256')!=c['source']['sha256'], 'F06 retained g6 input already appears in old ordinary history')
        records.append([path.name,digest(raw),len(raw)]); ids.append(row['id'])
    require(len(records)==512, 'F06 exact canonical512 basis changed; reconcile independently')
    return dict(records=records,run_ids=ids,manifest_sha256=digest(encoded(records)))


def custody():
    """Metadata only, token contents never opened; exact own run excluded by history.
    Names, ownership, size and nanosecond identity bind once/ingress/custody trees.
    Root semantic evidence separately pins actual old once/effect meaning.
    """
    records = []
    root = safe_path(STATE)
    def walk(p):
        entries = sorted(p.iterdir())
        for path in entries:
            if path==STATE/'runs':
                continue
            safe_path(path)
            info = path.lstat()
            require(info.st_uid==os.getuid() and not stat.S_IMODE(info.st_mode)&0o002
                    and (stat.S_ISREG(info.st_mode) and info.st_nlink==1 or stat.S_ISDIR(info.st_mode)),
                    'F06 tester once/ingress custody unsafe')
            require(len(records)<50000, 'F06 bounded custody metadata inventory exceeded')
            # Directory mtime naturally changes when the exact own pristine row is
            # created inside runs; runs is the only omitted subtree and is hashed above.
            records.append([str(path.relative_to(root)),identity(info)])
            if stat.S_ISDIR(info.st_mode):
                walk(path)
    walk(root)
    return dict(records=records,sha256=digest(encoded(records)),contents_read=False)


def observe(proof):
    """Finite future Root collector. This function is never invoked by preparation."""
    c,s = validate_effect(proof)
    installation(proof)
    services = {label:service(unit) for label,unit in
                [('gateway','hermes-gateway-1b7e7667.service'),('dashboard','hermes-dashboard.service')]}
    state,raw,kernel = gateway()
    require(services['gateway']['identity']==kernel, 'F06 service/state gateway mismatch')
    native = transport().fresh_native(state)
    require(native['identity']==kernel and native['session_id']==SID and native['session_key']==KEY,
            'F06 same-B native tuple mismatch')
    dbs = databases()
    hist = history(c,s)
    cursor = ref(STATE/'cursor.json',private=True)
    cursor['identity'] = identity((STATE/'cursor.json').stat())
    cursor_value = doc(STATE/'cursor.json',private=True)
    require(type(cursor_value) is dict and type(cursor_value.get('offset')) is int and cursor_value['offset']>=0,
            'F06 valid current cursor required')
    require(not os.path.lexists(STATE/'observer-stop.json'), 'F06 observer cancellation retained')
    cooldown = ref(STATE/'cooldown.json',private=True) if (STATE/'cooldown.json').exists() else None
    cool = readref(cooldown) if cooldown else {}
    until = cool.get('until',0)
    require(type(until) in (int,float) and math.isfinite(until) and time.time()>=until, 'F06 active retry_after cooldown')
    owned = custody()
    source_pin = ref(c['source']['path'],private=False)
    source_info = safe_path(c['source']['path']).stat()
    source_identity = dict(device=source_info.st_dev,inode=source_info.st_ino,size_bytes=source_info.st_size,
        uid=source_info.st_uid,mtime_ns=source_info.st_mtime_ns,ctime_ns=source_info.st_ctime_ns)
    require(source_identity==s['steps'][0]['input']['stat'], 'F06 scenario actual retained-input stat changed')
    require(source_pin==c['source'], 'F06 retained original g6 ciphertext changed')
    configs = {label:ref(path.parent/'config.yaml',private=False) for label,path in DATABASES.items()}
    require(read(H/'gateway_state.json')==raw and transport().kernel(kernel['pid'])==kernel,
            'F06 gateway CAS drift across metadata observation')
    boundary = dict(history_manifest_sha256=hist['manifest_sha256'],cursor_sha256=cursor['sha256'],
        native_boundary_sha256=digest(encoded(dbs)),once_sha256=owned['sha256'],
        ingress_lineage_sha256=digest(encoded(dict(source=source_pin,databases=dbs,custody=owned['sha256']))),
        gateway=kernel,B=dict(profile='telegram-bot-8812646969',session_id=SID,session_key=KEY,
        native_max_id=dbs['tester']['max_message_id']),phase_unconsumed=True,uploads_this_operation=1,producer_calls=0,restarts=0)
    return dict(installed_product=dict(EXPECTED),services=services,gateway=kernel,native_readonly=native,
        databases=dbs,history=hist,cursor=cursor,cooldown=cooldown,custody=owned,source=source_pin,
        profile_configs=configs,source_identity=source_identity,f06_mutable_boundary=boundary,all_profile_projection_limit=LIMIT)


def semantic(proof,c,actual):
    require(proof['history_semantic_review']==c['root_proofs']['all_profile_history_semantic_once']
            and proof['runtime_privacy_review']==c['root_proofs']['private_password_handling'], 'F06 immutable Root review refs differ')
    review = readref(proof['history_semantic_review'])
    require(review.get('schema')=='frw.Root.F06.history-semantic-once.v1' and review.get('operator')=='Root'
        and review.get('status')=='ROOT_BOUND' and review.get('phase')==c['phase']
        and review.get('source')==c['source']
        and review.get('history_manifest_sha256')==actual['history']['manifest_sha256']
        and review.get('classified_run_ids')==actual['history']['run_ids']
        and review.get('native_boundary_sha256')==actual['f06_mutable_boundary']['native_boundary_sha256']
        and review.get('once_sha256')==actual['f06_mutable_boundary']['once_sha256']
        and review.get('ingress_lineage_sha256')==actual['f06_mutable_boundary']['ingress_lineage_sha256']
        and review.get('equivalent_original_phase_effects')==[]
        and review.get('all_profile_history_and_compacted_unlogged_equivalents_reconciled') is True
        and review.get('old_effects_UNKNOWN_and_clocks_preserved') is True
        and review.get('M14_partial_UNKNOWN_preserved_no_replay_or_regrade') is True
        and review.get('all_profile_projection_limit')==LIMIT,
        'F06 exact allprofile/history/once semantic judgement absent or basis changed')
    retained = review.get('retained_basis')
    require(type(retained) is list and len(retained)>=2, 'F06 immutable original/history semantic basis refs required')
    for r in retained:
        reference(r)
    privacy = readref(proof['runtime_privacy_review'])
    require(privacy.get('schema')=='frw.Root.F06.installed207-runtime-privacy-review.v1'
        and privacy.get('operator')=='Root' and privacy.get('status')=='ROOT_BOUND'
        and privacy.get('installed_product')==EXPECTED
        and privacy.get('runtime_hashes')==RUNTIME_HASHES
        and privacy.get('genuine_installed_runtime_consumer_observed') is True
        and privacy.get('no_marker_or_import_bypass') is True
        and privacy.get('raw_user_chat_retention_separately_reviewed') is True
        and privacy.get('no_blanket_no_secret_persistence_claim') is True
        and privacy.get('Standard3_2_data_integrity_verified') is False,
        'F06 actual207 runtime privacy consumer Root acceptance absent')
    facts = privacy.get('runtime_evidence')
    require(type(facts) is list and len(facts)>=1, 'F06 genuine runtime privacy evidence absent')
    for r in facts:
        reference(r)



def disjoint(private_paths,effective_roots):
    require(type(effective_roots) is list and effective_roots==sorted(set(effective_roots))
            and len(effective_roots)>=1 and all(type(p) is str and canonical_path(p).is_absolute() for p in effective_roots), 'F06 source-derived effective roots required')
    require(str(H) in effective_roots, 'F06 installed home omitted from effective product roots')
    for private in private_paths:
        p = canonical_path(private)
        require(not any(p.is_relative_to(canonical_path(root))
                or canonical_path(root).is_relative_to(p) for root in effective_roots),
                'F06 private source/proof directory intersects effective product root')


def private_material(proof,c,actual,proof_path):
    """Verify pinned source-derived Root roots, never infer roots with a YAML parser.
    Root must produce this evidence from the unchanged actual consumer/configuration;
    copied source-only booleans cannot supply the required evidence/config hashes.
    """
    privacy = readref(proof['runtime_privacy_review'])
    roots = privacy.get('effective_product_roots')
    materials = [str(canonical_path(HERE)),str(canonical_path(proof_path).parent),str(canonical_path(c['scenario_ref']['path']).parent),
                 str(canonical_path(c['source']['path']).parent)]
    materials += [str(canonical_path(r['path']).parent) for r in c['root_proofs'].values()]
    materials += [str(canonical_path(c['resources'][k]['path']).parent) for k in ('clock','owned_parent_wait_cleanup')]
    protected = privacy.get('private_roots')
    require(type(protected) is list and protected==sorted(set(protected))
            and all(type(p) is str and canonical_path(p).is_absolute() for p in protected)
            and all(any(canonical_path(material).is_relative_to(canonical_path(p)) for p in protected) for material in materials),
            'F06 all exact private material directories must be covered by Root roots')
    disjoint(protected,roots)
    require(privacy.get('effective_roots_profile_config_refs')==actual['profile_configs'],
            'F06 effective-root source basis does not bind current allprofile configs')
    basis = privacy.get('effective_roots_source_basis')
    require(type(basis) is list and len(basis)>=1, 'F06 effective root consumer/source derivation evidence absent')
    for r in basis:
        reference(r)
    # Parent command/environment/config only checked for exact private directory
    # paths; no secret is returned or serialized by this checker.
    markers = [p.encode() for p in protected]
    for r in actual['profile_configs'].values():
        require(not any(p in reference(r,private=False) for p in markers), 'F06 private preparation directory in product profile config')
    for name in ('cmdline','environ'):
        raw = read_process(actual['gateway']['pid'],name)
        require(not any(p in raw for p in markers), 'F06 private preparation directory in gateway process')
    lineage = readref(c['root_proofs']['source_ingress_lineage'])
    require(lineage.get('schema')=='frw.Root.F06.retained-g6-source-lineage.v1'
        and lineage.get('operator')=='Root' and lineage.get('status')=='ROOT_BOUND'
        and lineage.get('phase')==c['phase'] and lineage.get('source')==c['source']
        and lineage.get('source_identity')==actual['source_identity']
        and lineage.get('current_ingress_lineage_sha256')==actual['f06_mutable_boundary']['ingress_lineage_sha256']
        and lineage.get('original_producer_g6_retained') is True
        and lineage.get('no_new_producer_or_native_repeat') is True
        and lineage.get('first_ordinary_upload_not_previously_consumed') is True
        and lineage.get('native_qualification')==c['root_proofs']['actual_native_qualification'],
        'F06 exact retained-g6/no-old-effect source and ingress lineage judgement absent')
    basis = lineage.get('retained_producer_oracle_basis')
    require(type(basis) is list and len(basis)>=1, 'F06 retained producer/oracle immutable lineage refs absent')
    for r in basis:
        reference(r)


def read_process(pid,name):
    require(type(pid) is int and pid>0 and name in ('cmdline','environ'), 'F06 bounded process metadata read only')
    p = Path('/proc')/str(pid)/name
    with p.open('rb') as stream:
        raw = stream.read(1024**2+1)
    require(len(raw)<=1024**2, 'F06 bounded process metadata exceeded')
    return raw


def shared_slot(owner):
    require(type(owner) is dict and set(owner)=={'pid','start_time','boot_id'}, 'F06 actual shared-slot owner required')
    p = safe_path(SLOT); info = p.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and info.st_nlink==1
            and stat.S_IMODE(info.st_mode)==0o600 and transport().kernel(owner['pid'])==owner,
            'F06 shared-slot owner custody changed')
    dev = f'{os.major(info.st_dev):02x}:{os.minor(info.st_dev):02x}:{info.st_ino}'
    require(any(len(v:=row.split())>=6 and v[1]=='FLOCK' and v[3]=='WRITE'
                and v[4]==str(owner['pid']) and v[5]==dev for row in Path('/proc/locks').read_text().splitlines()),
            'F06 Root does not hold existing exclusive shared slot')


def final_native(actual):
    require(databases()==actual['databases'], 'F06 current3DB metadata changed at final boundary')
    state,raw,kernel = gateway()
    require(kernel==actual['gateway'], 'F06 final gateway drift')
    native = transport().fresh_native(state)
    require(native==actual['native_readonly'] and read(H/'gateway_state.json')==raw,
            'F06 final fresh native generation/custody drift')
    return native


def check(proof_path, proof_sha256):
    require(sha(proof_sha256), 'F06 exact Root proof SHA required')
    proof = readref(dict(path=str(canonical_path(proof_path)),sha256=proof_sha256))
    deadline = validate_proof(proof)
    c,_ = validate_effect(proof)
    shared_slot(proof['shared_slot_owner'])
    actual = observe(proof)
    require(actual==proof['observed'], 'F06 mutable current207/history/cursor/once/custody facts changed')
    require(actual['f06_mutable_boundary']==c['boundary'] and actual['installed_product']==c['product']
            and actual['gateway']==c['boundary']['gateway'], 'F06 exact selected contract boundary changed')
    semantic(proof,c,actual)
    private_material(proof,c,actual,proof_path)
    native = final_native(actual)
    shared_slot(proof['shared_slot_owner'])
    require(time.monotonic()<deadline, 'F06 proof expired during current readback')
    fresh(proof)
    return dict(admission=False,installed_product=dict(c['product']),Root_proof_sha256=proof_sha256,
        f06_mutable_boundary=c['boundary'],whole_effect_sha256=proof['whole_effect_sha256'],
        gateway=actual['gateway'],native_readonly=native)


def unbound_proof():
    """Pure exact template; Root supplies real independently accepted metadata later.
    To avoid cycles contract_effect excludes authority/authority_id/status/currentproof.
    Root may reuse a semantic review only while every declared basis hash is identical.
    Collect metadata while holding the ordinary shared slot, bind c.boundary from it,
    then re-collect after the effect hash is fixed; never manufacture a live proof here.
    """
    return dict(schema=SCHEMA,status='UNBOUND_NOT_GRANTED',operator='Root',created_at=None,
        expires_at=None,created_monotonic=None,expires_monotonic=None,boot_id=None,
        contract_effect=None,whole_effect_sha256=None,installation_acceptance=None,
        installation_closure=dict(path=str(CLOSURE),sha256=CLOSURE_SHA),runtime_privacy_review=None,
        history_semantic_review=None,observed=None,shared_slot_owner=None)
