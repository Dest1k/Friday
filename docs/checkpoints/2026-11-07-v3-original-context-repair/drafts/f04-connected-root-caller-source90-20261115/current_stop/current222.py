"""Dormant Root F04 current222 + correlated native ownership seam.

Import performs no reads, query or effect. RuntimeLeaves is the real read-only
collector; tests substitute inert leaves explicitly. Source selection and a
prospective222 receipt never count as installed/current admission.
"""
import ast
import contextlib
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import time
import types

HOME = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
STATE = Path('/home/jericho/.local/share/friday-telegram-bot-test')
SLOT = Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
TECHNIQUE = {'path':'/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114/caller-root-json-r1/current/current221.py','bytes':39928,'sha256':'9d633e17a570fd485f262a88dcb1b4775a676c3a7a91956f5a4765521bd40f98'}
HELPER = {'path':'/home/jericho/.cache/FRW-SOL-V3-M09-FXDOC-PRIVACY-SOURCE-CORE-20261114/candidate-r2/private/root_m09.py','bytes':55948,'sha256':'1d03d4e2d310a5c8109a85daea8ab32d34b47b1eb897f0a9080990b61beec7fc'}
EXPECTED = dict(source_layers=222, project_files=525, native_files=17893, plugin_files=52, base_source_files=17730, source_receipt_sha256='b9bbf62464a86621b654f4034480a7e7ac2c280f19ab55b1d7908bd09ae06721', input_sha256='6ce2378edfb4f2e39fbac58f987ce7d66eaee0b7975c5bdffd0e210b46106951')
CAPTURE_REFS = {'path':'/home/jericho/.cache/FRW-ASTRA-SOL-T90-F04-ROOT-ORDINARY-CALLER-20261115/static-native-stop-source/SOURCE-REFS.json','bytes':1166,'sha256':'afb7713b2e9150d268bcd2fc524fbc384fb7547b7a97e8a7712ae71cc3643f64'}
PROJECTION_SOURCE = {'path':'/home/jericho/.cache/FRW-ASTRA-SOL-T90-F04-ROOT-ORDINARY-CALLER-20261115/static-native-stop-source/gateway/ordinary_turn_projection.py','bytes':41163,'sha256':'466c67eb3f70713c88573ff6b19ba623762b0e127dc031873f2ed70015ec2743'}
DISPATCH_SOURCE = {'path':'/home/jericho/.cache/FRW-ASTRA-SOL-T90-F04-ROOT-ORDINARY-CALLER-20261115/static-native-stop-source/gateway/run.py','bytes':334500,'sha256':'648579c87769629589ecb170289ca05600cad64273fda410919c5d0e4e7029b1'}
RUN_SHA = '648579c87769629589ecb170289ca05600cad64273fda410919c5d0e4e7029b1'
NATIVE_SHA = '466c67eb3f70713c88573ff6b19ba623762b0e127dc031873f2ed70015ec2743'
INSTALL_HELPER_SHA = '06fd2ab2ab96f9bced79a6d76a74fdc3f6886d468dcd8525a28422d89213ad43'
SOURCE_PATH = '/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114/input/orders-formulas-original.ods'
ROOT_SCOPE = 'case165/F04/format27_to26/original_required_rich_formula'
SOURCE_SHA = 'a2e68bc685e4d689aa7972ff4f2c7f9841441c9dcb4fc5e40327a5ae190b5d58'
SELECTION_SHA = '5287952d2ab0784f0ff6bd12e8ce8ed28f0691ed1f393be03ceff5abd6a76dbb'
NATIVE_TARGETS = {'tools/file_tools.py':'d040b2d08deb9d52aa9e2532474fc779e4dafbbe520fa43d124eb38f07b71c3a','tools/scoped_spreadsheet_rich.py':'b4f1751c0a50c0f106b4035826e02d2f4bc13a1632013d3e7aeac6385ee16462'}
BIND_KEYS = ('root_scope','operation_id','run_id','root_authority_id','scenario_ref','source','clock','resources','slot')
CURRENT_FIELDS = ('installed_product','canonical4','services','gateway','selected_scope','source_stat','history','databases','current_files','mutable_paths','historical_once','private_context','cancel_state','source_process')
REVIEWS = ('source_custody','all_profile_history_semantic_once','private_exclusion','owned_actor_stop_resources')
PHASES = ('NEW','CURSOR_AUTHORITY','PRE_INTENT_REVALIDATION')

class Refused(ValueError):
    pass

def need(ok, code):
    if not ok: raise Refused(code)

def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False)+'\n').encode()

def digest(raw): return hashlib.sha256(raw).hexdigest()

def unique(pairs):
    result={}
    for key,value in pairs:
        need(key not in result,'F04_DUPLICATE_JSON_KEY'); result[key]=value
    return result

def reference(value):
    return type(value) is dict and set(value)=={'path','bytes','sha256'} and type(value['path']) is str and Path(value['path']).is_absolute() and str(Path(value['path']))==value['path'] and '..' not in Path(value['path']).parts and type(value['bytes']) is int and 0<value['bytes']<=24*1024**2 and type(value['sha256']) is str and re.fullmatch('[a-f0-9]{64}',value['sha256']) is not None

def identity(info):
    return {k:getattr(info,'st_'+k) for k in ('dev','ino','uid','gid','mode','nlink','size','mtime_ns','ctime_ns')}

def read(path, *, private=False, limit=24*1024**2):
    p=Path(path)
    need(p.is_absolute() and '..' not in p.parts and not any(q.is_symlink() for q in (p,*p.parents)),'F04_ABSOLUTE_NO_LINK_PATH_REQUIRED')
    with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as f:
        before=os.fstat(f.fileno()); raw=f.read(limit+1); after=os.fstat(f.fileno())
    need(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1 and not stat.S_IMODE(before.st_mode)&0o002 and len(raw)<=limit and identity(before)==identity(after)==identity(p.stat()),'F04_FILE_CUSTODY_OR_CAS_CHANGED')
    if private:
        parent=p.parent.stat();need(stat.S_IMODE(before.st_mode)==0o600 and parent.st_uid==os.getuid() and stat.S_IMODE(parent.st_mode)==0o700,'F04_PROTECTED0600_0700_REQUIRED')
    return raw

def readref(ref, *, private=True):
    need(reference(ref),'F04_EXACT_REFERENCE_REQUIRED');raw=read(ref['path'],private=private)
    need(len(raw)==ref['bytes'] and digest(raw)==ref['sha256'],'F04_REFERENCE_CHANGED');return raw

def docref(ref, *, private=True):return json.loads(readref(ref,private=private),object_pairs_hook=unique)

def load(ref,name):
    raw=readref(ref,private=False);m=types.ModuleType(name);m.__file__=ref['path'];exec(compile(raw,ref['path'],'exec'),m.__dict__);return m

def stable_native(value):return {k:v for k,v in value.items() if k not in ('observed_monotonic','query_id')}

def binding(root):
    need(type(root) is dict and all(k in root for k in BIND_KEYS),'F04_ROOT_BINDING_UNBOUND')
    need(root['root_scope']==ROOT_SCOPE and type(root['operation_id']) is str and root['operation_id'] and 'UNBOUND' not in root['operation_id'],'F04_ORIGINAL_REQUIRED_SCOPE_UNBOUND')
    need(type(root['run_id']) is str and root['run_id'] and type(root['root_authority_id']) is str and root['root_authority_id'] and 'UNBOUND' not in root['root_authority_id'],'F04_ROOT_AUTHORITY_UNBOUND')
    need(all(reference(root[k]) for k in ('scenario_ref','source','clock')),'F04_ROOT_INPUT_REFS_UNBOUND')
    need(root['source']['path']==SOURCE_PATH and root['source']['sha256']==SOURCE_SHA and root['source']['bytes']==16538,'F04_ORIGINAL_SOURCE_REQUIRED')
    result={k:root[k] for k in BIND_KEYS}
    need(type(root['slot']) is dict and {'path','identity','owner'}<=set(root['slot']),'F04_SLOT_BINDING_UNBOUND')
    result['slot']={k:root['slot'][k] for k in ('path','identity')}
    need(type(root.get('once')) is dict and type(root['once'].get('path')) is str and Path(root['once']['path']).is_absolute(),'F04_ONCE_PATH_BINDING_UNBOUND')
    result['once_path']=root['once']['path']
    return result

def proof_shape(root,proof):
    need(type(proof) is dict and proof.get('schema')=='frw.Root.F04.current222.v1' and proof.get('operator')=='Root' and proof.get('status')=='ROOT_BOUND','F04_ROOT_FRESH_CURRENT_PROOF_REQUIRED')
    need(proof.get('binding')==binding(root),'F04_CURRENT_EFFECT_BINDING_CHANGED')
    need(root.get('boundary_phase') in PHASES,'F04_CURRENT_BOUNDARY_PHASE_REQUIRED')
    need(proof.get('installed_expected')==EXPECTED,'F04_PROSPECTIVE222_NOT_ACTUAL')
    need(reference(proof.get('installed_closure')) and reference(proof.get('native_request')) and type(proof.get('native_socket_path')) is str,'F04_ACTUAL_INSTALL_NATIVE_SELECTORS_UNBOUND')
    need(type(proof.get('current_files')) is list and proof['current_files'] and all(reference(x) for x in proof['current_files']) and len({x['path'] for x in proof['current_files']})==len(proof['current_files']),'F04_CURRENT_SOURCE_CONFIG_PINS_UNBOUND')
    paths=proof.get('mutable_paths');need(type(paths) is list and paths and all(type(x) is dict and set(x)=={'category','path'} and x['category'] in ('cancel','once','recovery','action_ownership') and type(x['path']) is str and Path(x['path']).is_absolute() for x in paths) and {x['category'] for x in paths}=={'cancel','once','recovery','action_ownership'} and len({x['path'] for x in paths})==len(paths),'F04_CANCEL_ONCE_RECOVERY_OWNERSHIP_SCOPE_UNBOUND')
    need(type(proof.get('root_reviews')) is dict and set(proof['root_reviews'])==set(REVIEWS)|{'original_selection'} and all(reference(x) for x in proof['root_reviews'].values()),'F04_ROOT_SEMANTIC_REVIEWS_UNBOUND')
    need(proof['root_reviews']['original_selection']['sha256']==SELECTION_SHA,'F04_EXACT_ORIGINAL_SELECTION_REQUIRED')
    need(type(proof.get('observed')) is dict and all(k in proof['observed'] for k in CURRENT_FIELDS+('native_readonly',)),'F04_REVIEWED_CURRENT_OBSERVATION_UNBOUND')

def lifetime(proof,leaves):
    wall,mono,boot=leaves.now()
    need(all(type(proof.get(k)) in (int,float) and math.isfinite(proof[k]) for k in ('created_at','expires_at','created_monotonic','expires_monotonic')),'F04_FINITE_CURRENT_LIFETIME_REQUIRED')
    need(proof['created_at']<=wall<proof['expires_at']<=proof['created_at']+120 and 0<=proof['created_monotonic']<=mono<proof['expires_monotonic']<=proof['created_monotonic']+120 and abs((wall-proof['created_at'])-(mono-proof['created_monotonic']))<=2 and proof.get('boot_id')==boot,'F04_CURRENT_PROOF_EXPIRED_OR_CLOCK_CHANGED')

def check_reviews(root,proof,actual,leaves):
    reviews={k:leaves.docref(v) for k,v in proof['root_reviews'].items()}
    # Selection is static metadata, explicitly separate from Root current approval.
    selection=reviews['original_selection'];need(selection.get('execution_grant') is False and selection.get('current_admission') is False,'F04_SELECTION_MUST_NOT_IMPERSONATE_CURRENT')
    for key in REVIEWS:
        row=reviews[key]
        need(row.get('schema')=='frw.Root.F04.'+key+'.v1' and row.get('operator')=='Root' and row.get('binding_sha256')==digest(encoded(binding(root))) and type(row.get('evidence')) is list and row['evidence'],'F04_EXACT_ROOT_REVIEW_REQUIRED_'+key)
        for ref in row['evidence']:leaves.readref(ref,private=False)
    custody=reviews['source_custody'];hist=reviews['all_profile_history_semantic_once'];privacy=reviews['private_exclusion'];owned=reviews['owned_actor_stop_resources']
    need(custody.get('source_ref')==root['source'] and custody.get('source_stat')==actual['source_stat'] and custody.get('selected_native_scope')==actual['selected_scope'] and all(custody.get(k) is True for k in ('same_authorized_principal','root_fixture_owned','principal_acl_reviewed','unchanged_source_required')) and custody.get('ordinary_ingress_existing_required') is False,'F04_SOURCE_CUSTODY_PERMISSION_UNBOUND')
    manifests={k:v['manifest_sha256'] for k,v in actual['databases'].items()}
    need(hist.get('history_manifest_sha256')==actual['history']['manifest_sha256'] and hist.get('native_manifests')==manifests and hist.get('once_sha256')==digest(encoded(actual['historical_once'])) and hist.get('mutable_paths_sha256')==digest(encoded(actual['mutable_paths'])) and hist.get('equivalent_original_phase_effects')==[] and hist.get('unresolved_original_phase_equivalents')==[] and all(hist.get(k) is True for k in ('all_profiles_and_compacted_unlogged_equivalents_reconciled','old_effects_UNKNOWN_and_clocks_preserved')) and hist.get('retained_effects')=={'R98':'CONSUMED','R100':'CONSUMED','F03':'CLOSED'},'F04_SEMANTIC_NONREPLAY_UNBOUND_OR_CONSUMED')
    need(privacy.get('history_manifest_sha256')==actual['history']['manifest_sha256'] and privacy.get('native_manifests')==manifests and privacy.get('current_files')==actual['current_files'] and privacy.get('private_context_sha256')==digest(encoded(actual['private_context'])) and all(privacy.get(k) is True for k in ('current_context_files_complete_for_selected_action','private_inputs_not_ingested_or_product_visible')),'F04_PRIVATE_CONTEXT_EXCLUSION_UNBOUND')
    need(owned.get('resources')==root['resources'] and owned.get('current_files')==actual['current_files'] and owned.get('native_implementation_sha256')==NATIVE_SHA and owned.get('cancel_state_sha256')==digest(encoded(actual['cancel_state'])) and all(owned.get(k) is True for k in ('mutable_paths_complete_for_action','cancel_root_only','no_old_effect_replay','new_effect_unconsumed','source_fixture_no_product_write')),'F04_OWNED_CANCEL_RESOURCE_REVIEW_UNBOUND')

def check_once(root,leaves):
    once=root.get('once');need(type(once) is dict and type(once.get('path')) is str and Path(once['path']).is_absolute(),'F04_ROOT_ONCE_UNBOUND')
    actual=leaves.inventory(once['path'])
    if root['boundary_phase']=='NEW':need(once.get('status')=='ABSENT' and actual=={'state':'ABSENT','path':once['path']},'F04_ONCE_ALREADY_EXISTS_RECONCILE_ONLY')
    else:
        need(once.get('status')=='CONSUMED' and reference(once.get('reference')) and once['reference']['path']==once['path'],'F04_ONCE_CONSUMED_EXACT_REF_REQUIRED')
        row=leaves.docref(once['reference'])
        need(row.get('schema')=='frw.Root.F04.once.v1' and row.get('operator')=='Root' and row.get('root_authority_id')==root['root_authority_id'] and row.get('run_id')==root['run_id'] and row.get('operation_id')==root['operation_id'] and row.get('scenario_sha256')==root['scenario_ref']['sha256'] and row.get('source_sha256')==root['source']['sha256'] and row.get('no_retry') is True,'F04_ONCE_EFFECT_CHANGED')
        need(actual.get('state')=='FILE' and actual.get('ref')==once['reference'],'F04_ONCE_CURRENT_CAS_CHANGED')
    return actual

def current_gate(root,leaves):
    need(type(root.get('current')) is dict and set(root['current'])=={'proof'} and reference(root['current']['proof']),'F04_CURRENT_UNBOUND_NO_EFFECT')
    proof=leaves.docref(root['current']['proof']);proof_shape(root,proof);require_owned_stop_capability(root,leaves);lifetime(proof,leaves)
    observed=leaves.observe(root,proof)
    for key in CURRENT_FIELDS:need(observed[key]==proof['observed'][key],'F04_CURRENT_CAS_CHANGED_'+key)
    need(stable_native(observed['native_readonly'])==stable_native(proof['observed']['native_readonly']),'F04_CURRENT_NATIVE_CAS_CHANGED')
    need(observed['installed_product']==EXPECTED,'F04_ACTUAL_INSTALLED222_REQUIRED')
    check_reviews(root,proof,observed,leaves);own=check_once(root,leaves);leaves.resources(root,proof,observed)
    again=leaves.observe(root,proof)
    for key in CURRENT_FIELDS:need(again[key]==observed[key],'F04_FINAL_CURRENT_CAS_CHANGED_'+key)
    need(stable_native(again['native_readonly'])==stable_native(observed['native_readonly']),'F04_FINAL_NATIVE_CAS_CHANGED');need(check_once(root,leaves)==own,'F04_FINAL_ONCE_CAS_CHANGED');leaves.resources(root,proof,again);leaves.readref(root['current']['proof']);lifetime(proof,leaves)
    return dict(schema='frw.Root.F04.current222-verified.v1',matched=True,current_digest=digest(encoded({k:observed[k] for k in CURRENT_FIELDS})),root_authority_id=root['root_authority_id'],native_ownership={'gateway':observed['gateway'],'selected_scope':observed['selected_scope'],'before_snapshot_sha256':digest(encoded(stable_native(observed['native_readonly']))),'actual_owned_turn':'UNBOUND_UNTIL_CORRELATED_INGRESS'},admission=False,runtime_acceptance=False)

class RuntimeLeaves:
    """Concrete dormant collectors. Constructing this object does no I/O."""
    def now(self):return time.time(),time.monotonic(),Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    def readref(self,ref,*,private=True):return readref(ref,private=private)
    def docref(self,ref,*,private=True):return docref(ref,private=private)
    def technique(self):return load(TECHNIQUE,'_F04_readonly_technique')
    def inventory(self,path):return self.technique().inventory(path)
    def observe(self,root,proof):
        t=self.technique();h=load(HELPER,'_F04_native_readonly_helper')
        closed=docref(proof['installed_closure'])
        need(closed.get('schema')=='frw.Root.actual222-installed-closed.v1' and closed.get('operator')=='Root' and closed.get('installed')==dict(layers=222,project=525,native=17893,plugins=52,base=17730) and all(closed.get(k) is True for k in ('actors_boundary_publisher_closed','healthy_services_infinity','full17893_readback_accepted')) and closed.get('source_only') is False,'F04_ACCEPTED_ACTUAL222_CLOSURE_REQUIRED')
        canonical={}
        for name in ('input','source_receipt','marker','stamp'):
            ref=closed['canonical4'][name];readref(ref,private=False);canonical[name]=ref
        need(canonical['input']['sha256']==EXPECTED['input_sha256'] and canonical['source_receipt']['sha256']==EXPECTED['source_receipt_sha256'],'F04_CURRENT_CANONICAL222_PINS_REQUIRED')
        receipt=docref(canonical['source_receipt'],private=False);marker=docref(canonical['marker'],private=False);stamp=docref(canonical['stamp'],private=False);inp=docref(canonical['input'],private=False)
        product=dict(source_layers=len(receipt['layers']),project_files=len(inp['project_files']),native_files=len(receipt['files']),plugin_files=len(marker['plugin_files']),base_source_files=receipt['source_file_count'],source_receipt_sha256=canonical['source_receipt']['sha256'],input_sha256=canonical['input']['sha256'])
        need(product==EXPECTED and marker['source_receipt_sha256']==EXPECTED['source_receipt_sha256'] and marker['input_sha256']==EXPECTED['input_sha256'] and stamp['fridaySource']['layers']==receipt['layers'] and stamp['fridaySource']['baseTree']==receipt['base_tree'],'F04_ACTUAL222_CANONICAL_TUPLE_CHANGED')
        pins={x['path']:x for x in proof['current_files']}
        required={str(HOME/'config.yaml'),str(HOME/'profiles/dest_telegram/config.yaml'),str(HOME/'profiles/telegram-bot-8812646969/config.yaml'),str(HOME/'plugin-data/agent-plugin-friday_rework-877e6505/state.json'),str(HOME/'profiles/dest_telegram/.friday-user-scope.json'),str(HOME/'profiles/telegram-bot-8812646969/.friday-user-scope.json'),str(HOME/'scripts/friday_ordinary_install.py')}
        required.update(str(HOME/'hermes-agent'/x) for x in t.CODE_MINIMUM+('tools/file_tools.py','tools/scoped_spreadsheet_rich.py','tools/scoped_spreadsheet.py','tools/scoped_ods_rich.py'))
        need(required<=set(pins),'F04_ACTIVE_ROUTE_PINS_INCOMPLETE')
        for ref in proof['current_files']:
            readref(ref,private=False);path=Path(ref['path'])
            if path.is_relative_to(HOME/'hermes-agent'):
                key=str(path.relative_to(HOME/'hermes-agent'));want=receipt['files'].get(key);need(want is not None and ref['sha256']==(want['sha256'] if type(want) is dict else want),'F04_CODE_NOT_ACTUAL_INSTALLED_SOURCE')
        for name,want in NATIVE_TARGETS.items():need(pins[str(HOME/'hermes-agent'/name)]['sha256']==want,'F04_TYPED_DISPATCHER_RICH_SOURCE_CHANGED')
        need(pins[str(HOME/'scripts/friday_ordinary_install.py')]['sha256']==INSTALL_HELPER_SHA and pins[str(HOME/'hermes-agent/gateway/ordinary_turn_projection.py')]['sha256']==NATIVE_SHA and pins[str(HOME/'hermes-agent/gateway/run.py')]['sha256']==RUN_SHA,'F04_INSTALL_NATIVE_HELPER_CHANGED')
        for name,want in marker['plugin_files'].items():
            need(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts and digest(read(HOME/name))==want,'F04_CURRENT_PLUGIN_ROUTE_CHANGED')
        units=t.services(closed,h)
        raw=read(HOME/'gateway_state.json');state=json.loads(raw,object_pairs_hook=unique);tg=state.get('platforms',{}).get('telegram',{})
        need(state.get('gateway_state')=='running' and state.get('active_agents')==0 and state.get('active_work') is None and state.get('restart_requested') is False and state.get('session_store',{}).get('status')=='ok' and tg.get('state')=='connected' and tg.get('needs_attention') is False and tg.get('writer_pid')==state.get('pid') and tg.get('writer_start_time')==state.get('start_time'),'F04_NATIVE_PREOP_NOT_HEALTHY_QUIESCENT')
        native,gateway=h.native(dict(native_request=proof['native_request'],native_socket_path=proof['native_socket_path'],native_implementation_sha256=NATIVE_SHA),state,raw,require_sessions=False)
        selected=native['scopes']['B'];t.selected_access(selected)
        scope={k:selected[k] for k in ('principal_id','profile','session_id','session_key','native_session_generation','access')}
        need(scope==proof['selected_scope'] and gateway==proof['gateway'],'F04_CURRENT_ROUTE_PRINCIPAL_CHANGED')
        need(state.get('hermes_home')==str(HOME) and state.get('argv')==[str(HOME/'hermes-agent/hermes_cli/main.py'),'gateway','run'],'F04_SUPPORTED_ACCOUNT_SOURCE_HOME_CHANGED')
        codepins=[r for r in proof['current_files'] if Path(r['path']).is_relative_to(HOME/'hermes-agent')]
        newest=max(max(Path(r['path']).stat().st_mtime_ns,Path(r['path']).stat().st_ctime_ns) for r in codepins)
        epoch=time.time()-float(Path('/proc/uptime').read_text().split()[0])+gateway['start_time']/os.sysconf('SC_CLK_TCK')
        need(epoch*1e9>newest,'F04_GATEWAY_PROCESS_PREDATES_INSTALLED_SOURCE')
        scenario=docref(root['scenario_ref']);need(digest(encoded(scenario))==root['scenario_ref']['sha256'],'F04_CANONICAL_SCENARIO_CHANGED')
        source_raw=readref(root['source']);info=Path(root['source']['path']).stat();source_stat={k:getattr(info,'st_'+{'device':'dev','inode':'ino','size_bytes':'size'}.get(k,k)) for k in ('device','inode','size_bytes','uid','mtime_ns','ctime_ns')}
        item=scenario['steps'][0]['input'];need(item.get('kind')=='document' and item.get('path')==root['source']['path'] and item.get('sha256')==SOURCE_SHA and item.get('mime_type')=='application/vnd.oasis.opendocument.spreadsheet' and source_stat==item['stat'] and len(source_raw)==16538,'F04_FRESH_SOURCE_STAT_CHANGED')
        privacy=docref(proof['root_reviews']['private_exclusion']);roots=privacy.get('private_roots');visible=privacy.get('effective_product_roots')
        need(type(roots) is list and roots and type(visible) is list and visible,'F04_PRIVATE_PRODUCT_ROOTS_UNBOUND')
        required_roots={str(Path(root[k]['path']).parent) for k in ('scenario_ref','source','clock')};required_roots.update(str(Path(r['path']).parent) for r in proof['root_reviews'].values());required_roots.update((str(Path(proof['native_request']['path']).parent),str(Path(root['current']['proof']['path']).parent),str(Path(proof['installed_closure']['path']).parent),str(Path(root['workdir']))))
        required_roots.update(str(Path(root[k]['path']).parent) for k in ('current_stop','source_freeze','independent_review') if reference(root.get(k)))
        need(required_roots<=set(roots),'F04_PRIVATE_ROOT_SET_INCOMPLETE')
        for p in roots+visible:
            q=Path(p);need(type(p) is str and q.is_absolute() and str(q)==p and '..' not in q.parts and not any(x.is_symlink() for x in (q,*q.parents)) and q.is_dir(),'F04_PRIVATE_PRODUCT_NO_ALIAS_REQUIRED')
        need(all(not Path(a).is_relative_to(Path(b)) and not Path(b).is_relative_to(Path(a)) for a in roots for b in visible),'F04_PRIVATE_PRODUCT_ROOT_OVERLAP')
        markers=tuple(x.encode() for x in roots);context=[]
        for leaf in ('cmdline','environ'):
            value=(Path('/proc')/str(gateway['pid'])/leaf).read_bytes()
            if leaf=='environ':need(b'HERMES_HOME='+str(HOME).encode() in value.split(b'\0'),'F04_ACCOUNT_PROCESS_HOME_CHANGED')
            else:need(str(HOME/'hermes-agent').encode() in value,'F04_ACCOUNT_PROCESS_SOURCE_CHANGED')
            need(len(value)<=1024**2 and not any(x in value for x in markers),'F04_PRIVATE_ROOT_IN_PRODUCT_PROCESS');context.append([leaf,len(value),digest(value)])
        for ref in proof['current_files']+privacy.get('current_context_files',[]):
            value=readref(ref,private=False);need(not any(x in value for x in markers),'F04_PRIVATE_ROOT_IN_PRODUCT_CONTEXT');context.append([ref['path'],len(value),digest(value)])
        databases={slot:t.database(slot,markers,native['scopes'].get(slot)) for slot in t.PROFILE_HOMES}
        routes=[row for row in databases['default']['routes'] if row[0]==str(HOME/'sessions') and row[1]==scope['session_key']]
        need(len(routes)==1,'F04_SELECTED_ROUTE_MISSING');route=json.loads(routes[0][2],object_pairs_hook=unique)
        need(route.get('session_id')==scope['session_id'] and route.get('session_key')==scope['session_key'] and route.get('platform')=='telegram' and route.get('chat_type')=='dm' and route.get('transport_profile','default')=='default' and not route.get('active_turn_token') and not route.get('pending_command_text') and not route.get('resume_pending'),'F04_SELECTED_ROUTE_PENDING_FOREIGN_ACTION')
        hist=self.history(root,scenario)
        need(not (STATE/'observer-stop.json').exists(),'F04_OBSERVER_STOP_RETAINED')
        if (STATE/'cooldown.json').exists():need(time.time()>=docref({'path':str(STATE/'cooldown.json'),'bytes':len(read(STATE/'cooldown.json',private=True)),'sha256':digest(read(STATE/'cooldown.json',private=True))}).get('until',math.inf),'F04_COOLDOWN_RETAINED')
        # Own ONCE is checked separately across its one allowed ABSENT->CONSUMED
        # transition; the reviewed historical inventories never include its path.
        need(all(Path(row['path'])!=Path(root['once']['path']) and not Path(root['once']['path']).is_relative_to(Path(row['path'])) for row in proof['mutable_paths']),'F04_OWN_ONCE_MUST_BE_SEPARATE_FROM_RETAINED_INVENTORY')
        paths=[{'category':x['category'],'value':t.inventory(x['path'])} for x in proof['mutable_paths']]
        recovery=set(closed['related_recovery_data_cutoff_scope']['related_recovery_state_paths']);need(recovery<={x['path'] for x in proof['mutable_paths'] if x['category']=='recovery'},'F04_RETAINED_RECOVERY_SCOPE_INCOMPLETE')
        once={x:t.inventory(STATE/x) for x in ('continuations','reconciliations')}
        need(read(HOME/'gateway_state.json')==raw,'F04_GATEWAY_STATE_FINAL_CAS_CHANGED')
        return dict(installed_product=product,canonical4=canonical,services=units,gateway=gateway,selected_scope=scope,source_stat=source_stat,history=hist,databases=databases,current_files=proof['current_files'],mutable_paths=paths,historical_once=once,private_context=context,cancel_state=[x for x in paths if x['category'] in ('cancel','action_ownership','recovery')],source_process={'gateway':gateway,'newest_selected_source_ns':newest,'home':str(HOME),'argv':state['argv']},native_readonly=native)
    def history(self,root,scenario):
        cursor_raw=read(STATE/'cursor.json',private=True);cursor=json.loads(cursor_raw,object_pairs_hook=unique);need(type(cursor.get('offset')) is int and cursor['offset']>=0,'F04_CURSOR_UNBOUND')
        paths=sorted((STATE/'runs').glob('*.json'));need(len(paths)<=2048,'F04_HISTORY_BOUND');records=[]
        for p in paths:
            raw=read(p,private=True,limit=1024**2);row=json.loads(raw,object_pairs_hook=unique);need(row.get('id')==p.stem and encoded(row)==raw,'F04_HISTORY_CANONICAL_ID_CHANGED')
            # Top-level caller has not created a tester run at any of its gates.
            need(row['id']!=root['run_id'],'F04_EXISTING_RUN_RECONCILE_ONLY');records.append([p.name,len(raw),digest(raw),row.get('status'),row.get('send_state')])
        need(not list(STATE.glob('send-task-'+root['run_id']+'-*')),'F04_SEND_INTENT_EXISTS_RECONCILE_ONLY')
        return dict(records=records,manifest_sha256=digest(encoded(records)),cursor=dict(path=str(STATE/'cursor.json'),bytes=len(cursor_raw),sha256=digest(cursor_raw)))
    def resources(self,root,proof,observed):
        clock=docref(root['clock']);wall,mono,boot=self.now()
        need(clock.get('schema')=='frw.Root.F04.original-clock.v1' and clock.get('operation_id')==root['operation_id'] and clock.get('operator')=='Root' and clock.get('run_id')==root['run_id'] and clock.get('boot_id')==boot and all(type(clock.get(k)) in (int,float) and math.isfinite(clock[k]) for k in ('origin_wall','deadline_wall','origin_monotonic','deadline_monotonic')),'F04_ORIGINAL_CLOCK_UNBOUND')
        need(clock['origin_wall']<=wall<clock['deadline_wall']<=clock['origin_wall']+600 and 0<=clock['origin_monotonic']<=mono<clock['deadline_monotonic']<=clock['origin_monotonic']+600 and abs((wall-clock['origin_wall'])-(mono-clock['origin_monotonic']))<=2 and min(clock['deadline_wall']-wall,clock['deadline_monotonic']-mono)>=305,'F04_ORIGINAL600_OR_300_RESERVE_EXHAUSTED')
        need(root.get('state_dir')==str(STATE),'F04_CANONICAL_STATE_REQUIRED');slot=root['slot'];need(slot.get('path')==str(SLOT),'F04_EXISTING_SLOT_REQUIRED')
        t=self.technique();h=load(HELPER,'_F04_slot_kernel');owner=slot['owner'];actual=h.kernel(os.getpid())
        need(type(owner) is dict and owner.get('pid')==os.getpid() and owner.get('starttime')==actual['start_time'] and owner.get('pgid')==os.getpgid(os.getpid()),'F04_ACTUAL_CALLER_SLOT_OWNER_CHANGED')
        t.shared_slot(actual,h)
        info=SLOT.stat();need(slot.get('identity')=={'device':info.st_dev,'inode':info.st_ino,'uid':info.st_uid,'mode':stat.S_IMODE(info.st_mode),'nlink':info.st_nlink},'F04_SHARED_SLOT_IDENTITY_CHANGED')
        # Existing tester canonical token and consumer locks must be free before
        # birth. Lock probes are transient, nonblocking, and close immediately.
        import fcntl
        for leaf in ('consumer.lock','tester-token'):
            p=STATE/leaf;need(not any(x.is_symlink() for x in (p,*p.parents)),'F04_CANONICAL_LOCK_LINK');fd=os.open(p,os.O_RDWR|os.O_NOFOLLOW)
            try:
                z=os.fstat(fd);need(stat.S_ISREG(z.st_mode) and z.st_uid==os.getuid() and z.st_nlink==1 and stat.S_IMODE(z.st_mode)==0o600,'F04_CANONICAL_LOCK_CUSTODY_CHANGED');fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            finally:os.close(fd)
        need(clock.get('cleanup_deadline_wall')==clock['deadline_wall'] and clock.get('cleanup_deadline_monotonic')==clock['deadline_monotonic'],'F04_FIXED_CLEANUP_ENDPOINTS_CHANGED')
        r=root['resources'];need(type(r.get('cleanup_seconds')) is int and 1<=r['cleanup_seconds']<=60,'F04_CLEANUP_RESERVE_INSIDE_OUTER_REQUIRED');need(r.get('reserve_seconds')==5 and r.get('ordinary_seconds')==300 and r.get('full_capture_seconds')==180 and r.get('ack_seconds')==10,'F04_ORIGINAL_BUDGETS_CHANGED')
        mem=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024;fs=os.statvfs(STATE)
        need(mem>=r['max_rss_bytes'] and fs.f_bavail*fs.f_frsize>=r['disk_bytes'] and os.sched_getaffinity(0),'F04_RESOURCES_UNAVAILABLE')

# No guessed live stop command is present. Exact existing source capture is a
# prerequisite of the first current gate, before ONCE/authority/Runner.new.
def require_owned_stop_capability(root,leaves):
    value=leaves.owned_stop_capability(root)
    need(type(value) is dict and value.get('schema')=='frw.source.F04.exact-owned-stop-capability.v1' and value.get('native_implementation_sha256')==NATIVE_SHA and reference(value.get('dispatch_source')) and reference(value.get('projection_source')) and value['projection_source']['sha256']==NATIVE_SHA,'STOP_API_SOURCE_CAPTURE_REQUIRED')
    need(value.get('implemented') is True,value.get('assertcode') if value.get('assertcode') in ('F04_STOP_API_SCOPE_UNSUPPORTED','F04_TYPED_INGRESS_ARTIFACT_TERMINAL_BRIDGE_UNAVAILABLE') else 'STOP_API_SOURCE_CAPTURE_REQUIRED')
    return value

def native_tuple(snapshot,seed):
    """Validate existing generic readonly tuple, independently of tester IDs."""
    need(type(snapshot) is dict and snapshot.get('schema')=='frw.gateway.ordinary-turn-readonly.v1' and snapshot.get('read_only') is True,'F04_GENUINE_NATIVE_TUPLE_REQUIRED')
    gateway=seed['gateway'];scope=seed['selected_scope']
    need(snapshot.get('answering_pid')==gateway['pid'] and snapshot.get('birth_ticks')==gateway['start_time'] and snapshot.get('boot_id')==gateway['boot_id'] and snapshot.get('implementation_sha256')==NATIVE_SHA,'F04_OWNED_NATIVE_WRITER_CHANGED')
    need(snapshot.get('session_id')==scope['session_id'] and snapshot.get('session_key')==scope['session_key'] and type(snapshot.get('generation')) is int and snapshot['generation']>=scope['native_session_generation'],'F04_OWNED_NATIVE_SCOPE_CHANGED')
    fields=('active','active_session_keys','turn_tokens','event_message_id','ctx_inbound_message_id','ctx_generation','pending_messages','active_adapters','adapter_generations','queued_events','pending_command','approvals','detached_owned_work','live_owned_delegations','durable_pending_delegations','web_custody','terminal_custody','own_web_inflight')
    need(all(k in snapshot for k in fields),'F04_OWNED_NATIVE_TUPLE_INCOMPLETE')
    return {k:snapshot[k] for k in ('session_id','session_key','generation')+fields}

def correlate_owned_tuple(root,received,snapshot,bridge):
    """Exact captured active native tuple shape. This validates a separately
    established source bridge, never equality across tester/native namespaces.
    The captured API exposes no completed-turn/artifact bridge: idle refuses.
    """
    ownership=received.get('ownership');need(type(ownership) is dict and type(ownership.get('native_ownership')) is dict,'F04_ACTUAL_ACTOR_NATIVE_SEED_REQUIRED')
    seed=ownership['native_ownership'];row=native_tuple(snapshot,seed)
    need(type(bridge) is dict and bridge.get('schema')=='frw.source.F04.correlated-owned-tuple.v1' and bridge.get('root_binding_sha256')==digest(encoded(binding(root))) and type(bridge.get('evidence')) is list and bridge['evidence'],'F04_CORRELATED_NATIVE_BRIDGE_REQUIRED')
    target=bridge.get('target');need(type(target) is dict and set(target)=={'session_id','session_key','generation','lease','event_message_id','ctx_inbound_message_id'},'F04_EXACT_OWNED_TURN_TARGET_REQUIRED')
    scope=seed['selected_scope'];lease=target['lease']
    need(target['session_id']==scope['session_id'] and target['session_key']==scope['session_key'] and type(target['generation']) is int and target['generation']>scope['native_session_generation'] and type(lease) is dict and lease=={'session_id':scope['session_id'],'owner_key':scope['session_key'],'generation':target['generation'],'released':False} and type(target['event_message_id']) is str and target['event_message_id'] and target['ctx_inbound_message_id'] is not None,'F04_OWNED_INGRESS_GENERATION_LEASE_UNBOUND')
    need(bridge.get('tester_message_id')==received.get('sent_message_id') and type(received.get('sent_message_id')) is int and bridge.get('source_sha256')==root['source']['sha256'] and bridge.get('scenario_sha256')==root['scenario_ref']['sha256'],'F04_ACTUAL_INGRESS_SOURCE_JOIN_UNBOUND')
    # Captured _cancel_compare compares native DB platform_message_id with both
    # event and ctx fields. It supplies no mapping from tester message IDs.
    need(str(target['ctx_inbound_message_id'])==target['event_message_id'],'F04_NATIVE_EVENT_CTX_MISMATCH')
    need(row['active'] is True,'F04_TYPED_TERMINAL_BRIDGE_UNAVAILABLE')
    need(row['generation']==target['generation'] and row['ctx_generation']==target['generation'] and row['event_message_id']==target['event_message_id'] and row['ctx_inbound_message_id']==target['ctx_inbound_message_id'] and row['turn_tokens']==[lease] and row['active_session_keys']==[scope['session_key']] and row['active_adapters']==1 and row['adapter_generations']==[target['generation']] and row['pending_messages']==0 and row['queued_events']==0 and row['pending_command'] is False and row['approvals'] is False and not row['live_owned_delegations'] and not row['durable_pending_delegations'],'F04_ACTIVE_TURN_NOT_CORRELATED_OWNED')
    return target

def native_resources_closed(snapshot,target):
    for key in ('active','active_session_keys','turn_tokens','event_message_id','ctx_inbound_message_id','ctx_generation','pending_messages','active_adapters','adapter_generations','queued_events','pending_command','approvals','detached_owned_work','live_owned_delegations','durable_pending_delegations'):
        if key not in snapshot or snapshot[key]:return False
    for key in ('web_custody','terminal_custody'):
        row=snapshot.get(key,{});
        if row.get('status')!='QUIESCENT' or row.get('sessions')!=[] or row.get('recovery_blocked') is not False:return False
    row=snapshot.get('own_web_inflight',{})
    return row.get('session_id')==target['session_id'] and row.get('session_key')==target['session_key'] and row.get('generation')==snapshot['generation'] and snapshot['generation']>=target['generation'] and row.get('recovery_blocked') is False and row.get('sessions')==[] and row.get('unretained_calls')==[] and all(row.get(k) is None for k in ('event_message_id','task_id','turn_id','user_authority'))

def cleanup_remaining(root,ownership,leaves):
    clock=ownership.get('clock');need(type(clock) is dict and clock==leaves.docref(root['clock']),'F04_ORIGINAL_CLEANUP_CLOCK_CHANGED')
    wall,mono,boot=leaves.now()
    need(clock.get('schema')=='frw.Root.F04.original-clock.v1' and clock.get('operator')=='Root' and clock.get('operation_id')==root['operation_id'] and clock.get('run_id')==root['run_id'] and clock.get('boot_id')==boot,'F04_ORIGINAL_CLEANUP_OWNERSHIP_CHANGED')
    keys=('origin_wall','deadline_wall','origin_monotonic','deadline_monotonic','cleanup_deadline_wall','cleanup_deadline_monotonic')
    need(all(type(clock.get(k)) in (int,float) and math.isfinite(clock[k]) for k in keys),'F04_FINITE_CLEANUP_CLOCK_REQUIRED')
    need(clock['origin_wall']<=wall and 0<=clock['origin_monotonic']<=mono and clock['deadline_wall']<=clock['origin_wall']+600 and clock['deadline_monotonic']<=clock['origin_monotonic']+600 and clock['cleanup_deadline_wall']==clock['deadline_wall'] and clock['cleanup_deadline_monotonic']==clock['deadline_monotonic'] and abs((wall-clock['origin_wall'])-(mono-clock['origin_monotonic']))<=2,'F04_FIXED_CLEANUP_ENDPOINTS_CHANGED')
    remaining=min(clock['cleanup_deadline_wall']-wall,clock['cleanup_deadline_monotonic']-mono);need(remaining>0,'F04_ORIGINAL_CLEANUP_DEADLINE_EXHAUSTED');return remaining

def verify_bridge_refs(bridge,leaves):
    for ref in bridge.get('evidence',[]):leaves.readref(ref,private=False)
    terminal=bridge.get('terminal_record')
    if type(terminal) is dict and reference(terminal.get('reference')):leaves.readref(terminal['reference'],private=False)

def stop_owned(root,ownership,leaves):
    """At most one source-proved exact owned native stop, never a retry loop."""
    try:
        require_owned_stop_capability(root,leaves)
        need(type(ownership) is dict and type(ownership.get('received')) is dict,'F04_UNSCOPED_OWNED_TURN_NO_STOP')
        cleanup_remaining(root,ownership,leaves)
        received=dict(ownership['received'],ownership={k:v for k,v in ownership.items() if k!='received'})
        snapshot=leaves.owned_snapshot(root,ownership);bridge=leaves.correlation_bridge(root,received,snapshot)
        target=correlate_owned_tuple(root,received,snapshot,bridge);verify_bridge_refs(bridge,leaves)
        # leaves.stop_exact is a source-pinned thin API binding; no verb or params
        # are accepted from Root JSON. Until capture, production refuses PREOP.
        cleanup_remaining(root,ownership,leaves);receipt=leaves.stop_exact(root,target,ownership)
        need(type(receipt) is dict and receipt.get('accepted') is True and receipt.get('sent_once') is True and receipt.get('transport')=='existing_gateway_control_socket' and receipt.get('session_id')==target['session_id'] and receipt.get('generation_before')==target['generation'] and type(receipt.get('generation_after')) is int and receipt['generation_after']>target['generation'] and type(receipt.get('native_dispatch_id')) is str and re.fullmatch('[a-f0-9]{64}',receipt['native_dispatch_id']) and receipt.get('settlement')=='REQUIRES_FRESH_INDEPENDENT_OBSERVATION' and receipt.get('telegram_stop_message_created') is False,'F04_EXACT_OWNED_STOP_UNCONFIRMED')
        after=leaves.owned_snapshot(root,ownership);native_tuple(after,ownership['native_ownership']);need(after['generation']==receipt['generation_after'],'F04_OWNED_STOP_POST_GENERATION_CAS_CHANGED')
        # Captured API explicitly invalidates generation before settlement and
        # requires independent post observation. No typed completed-turn/artifact
        # bridge is exposed. A success receipt, newer generation or generic idle
        # cannot establish this F04's own native completion.
        return dict(confirmed=False,state='OWNED_STOP_SETTLEMENT_UNASSESSED',assertcode='F04_TYPED_TERMINAL_BRIDGE_UNAVAILABLE',stop_sent=True,native_generation_after=after['generation'],retry_authorized=False)

    except Refused as exc:
        return dict(confirmed=False,state='OWNED_STOP_UNCONFIRMED',assertcode=str(exc),retry_authorized=False)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        return dict(confirmed=False,state='OWNED_STOP_UNCONFIRMED',assertcode='F04_OWNED_STOP_OBSERVATION_ERROR',failure_class=type(exc).__name__,retry_authorized=False)

def owned_closure(root,received,leaves):
    try:
        require_owned_stop_capability(root,leaves)
        need(type(received) is dict and type(received.get('ownership')) is dict,'F04_CLOSURE_ACTOR_OWNERSHIP_UNBOUND')
        cleanup_remaining(root,received['ownership'],leaves)
        snapshot=leaves.owned_snapshot(root,received['ownership']);bridge=leaves.correlation_bridge(root,received,snapshot);target=correlate_owned_tuple(root,received,snapshot,bridge);verify_bridge_refs(bridge,leaves)
        need(native_resources_closed(snapshot,target),'F04_NATIVE_ASSOCIATIONS_RESOURCES_NOT_CLOSED')
        # This checks actual canonical run + actual received saved artifact joins
        # and post-reap token/consumer locks; terminal EVIDENCE_READY alone never
        # claims native product completion or semantic/App/formal acceptance.
        custody=leaves.received_custody(root,received,bridge)
        need(custody.get('full180') is True and custody.get('actual_artifact_join') is True and custody.get('actor_absent') is True and custody.get('canonical_locks_free') is True,'F04_ACTUAL_CUSTODY_ACTOR_LOCK_CLOSURE_UNBOUND')
        return dict(closed=True,confirmed=True,state='CORRELATED_NATIVE_ACTOR_ARTIFACT_LOCKS_CLOSED',target_sha256=digest(encoded(target)),semantic_acceptance=False,retry_authorized=False)
    except Refused as exc:
        return dict(closed=False,confirmed=False,state='OWNED_CLOSURE_UNCONFIRMED',assertcode=str(exc),retry_authorized=False)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        return dict(closed=False,confirmed=False,state='OWNED_CLOSURE_UNCONFIRMED',assertcode='F04_OWNED_CLOSURE_OBSERVATION_ERROR',failure_class=type(exc).__name__,retry_authorized=False)

def inspect_owned_stop_source():
    """Static source-only capability inspection. Never import either gateway
    module: projection import itself reads its source; full run import is banned.
    The pins make the exact reviewed AST/contract immutable, without JSON flags.
    """
    manifest=docref(CAPTURE_REFS,private=False)
    need(manifest.get('source_only') is True and manifest.get('no_runtime_query_or_effect') is True,'F04_STATIC_STOP_CAPTURE_REQUIRED')
    for key,ref in (('gateway/ordinary_turn_projection.py',PROJECTION_SOURCE),('gateway/run.py',DISPATCH_SOURCE)):
        row=manifest.get('files',{}).get(key,{});need(all(row.get(k)==ref[k] for k in ('path','bytes','sha256')),'F04_STATIC_STOP_CAPTURE_PIN_CHANGED')
    projection=readref(PROJECTION_SOURCE,private=False);dispatch=readref(DISPATCH_SOURCE,private=False)
    tree=ast.parse(projection);functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    need({'snapshot','ordinary_turn_readonly_verb','ordinary_turn_cancel_verb','_cancel_compare','_checked_root_intent','_leases_and_user'}<=set(functions),'F04_STATIC_STOP_API_CONTRACT_CHANGED')
    cancel=ast.get_source_segment(projection.decode(),functions['ordinary_turn_cancel_verb']);compare=ast.get_source_segment(projection.decode(),functions['_cancel_compare']);snapshot=ast.get_source_segment(projection.decode(),functions['snapshot'])
    need("'ordinary-turn-cancel': ordinary_turn_cancel_verb" in dispatch.decode().replace('"',"'") and "frw.Root.s05-owned-native-stop.v1" in cancel and "root-(?:s05|s07|v01" in cancel and 'v04' in cancel and 'f04' not in cancel.lower() and 'os.O_EXCL' in cancel and cancel.count('_cancel_compare(')==2 and "_interrupt_and_clear_session" in cancel,'F04_STATIC_STOP_API_CONTRACT_CHANGED')
    need("current['turn_tokens']!=[dict(session_id=SID,owner_key=KEY,generation=own['generation'],released=False)]" in compare and "users[0]['platform_message_id']" in compare and "ctx.inbound_message_id" in snapshot and "str(event.message_id)" in snapshot,'F04_STATIC_OWNED_TUPLE_CONTRACT_CHANGED')
    return dict(schema='frw.source.F04.exact-owned-stop-capability.v1',implemented=False,source_verified=True,assertcode='F04_STOP_API_SCOPE_UNSUPPORTED',native_implementation_sha256=NATIVE_SHA,projection_source=dict(PROJECTION_SOURCE),dispatch_source=dict(DISPATCH_SOURCE),captured_verb='ordinary-turn-cancel',captured_schema='frw.Root.s05-owned-native-stop.v1',supported_operation_prefixes=['root-s05-','root-s07-','root-v01-','root-v01-text-','root-v02-','root-v02-text-','root-v03-','root-v03-text-','root-v04-','root-v04-text-'],F04_relabel_permitted=False,typed_ingress_artifact_terminal_bridge=False)

def _runtime_owned_stop_capability(self,root):
    return inspect_owned_stop_source()

def _runtime_owned_snapshot(self,root,ownership):
    """Concrete existing generic readonly transport. No query during import/tests.
    Peercred, mono, kernel and gateway_state CAS bind the exact answering writer.
    It intentionally permits an active own tuple; it grants no stop permission.
    """
    import socket
    import struct
    proof=docref(root['current']['proof']);seed=ownership['native_ownership'];expected=seed['gateway'];scope=seed['selected_scope']
    h=load(HELPER,'_F04_owned_kernel');need(h.kernel(expected['pid'])==expected,'F04_OWNED_WRITER_KERNEL_CHANGED')
    raw=read(HOME/'gateway_state.json');state=json.loads(raw,object_pairs_hook=unique)
    need(state.get('pid')==expected['pid'] and state.get('start_time')==expected['start_time'],'F04_OWNED_WRITER_STATE_CHANGED')
    path=Path(proof['native_socket_path']);direct=HOME/'gateway.sock'
    if path!=direct:need(read(HOME/'gateway.sock.path').decode().strip()==str(path),'F04_OWNED_SOCKET_POINTER_CHANGED')
    info=path.lstat();need(stat.S_ISSOCK(info.st_mode) and info.st_uid==os.getuid() and not stat.S_IMODE(info.st_mode)&0o077 and not any(p.is_symlink() for p in (path,*path.parents)),'F04_OWNED_NATIVE_SOCKET_ACL')
    query={'protocol':1,'id':'f04-owned-readonly-'+str(os.getpid()),'verb':'ordinary-turn-readonly','params':{'session_key':scope['session_key'],'session_id':scope['session_id']}}
    remaining=cleanup_remaining(root,ownership,self);before=time.monotonic();read_deadline=before+min(2,remaining)
    with socket.socket(socket.AF_UNIX) as sock:
        sock.settimeout(max(0.001,read_deadline-time.monotonic()));sock.connect(str(path));pid,uid,_=struct.unpack('3i',sock.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12));need(pid==expected['pid'] and uid==os.getuid(),'F04_OWNED_NATIVE_PEERCRED')
        sock.sendall(encoded(query));data=b''
        while not data.endswith(b'\n'):
            need(time.monotonic()<read_deadline,'F04_OWNED_NATIVE_QUERY_DEADLINE');sock.settimeout(max(0.001,read_deadline-time.monotonic()));chunk=sock.recv(65536);need(chunk and len(data)+len(chunk)<=512*1024,'F04_OWNED_NATIVE_FRAME_BOUND');data+=chunk
    after=time.monotonic();value=json.loads(data,object_pairs_hook=unique)
    need(data.count(b'\n')==1 and value.get('id')==query['id'] and value.get('ok') is True and value.get('result',{}).get('accepted') is True,'F04_OWNED_NATIVE_QUERY_REFUSED')
    snapshot=value['result']['snapshot'];native_tuple(snapshot,seed)
    need(type(snapshot.get('observed_monotonic')) in (int,float) and before<=snapshot['observed_monotonic']<=after and after-before<=3 and h.kernel(expected['pid'])==expected and read(HOME/'gateway_state.json')==raw,'F04_OWNED_NATIVE_FRESH_KERNEL_STATE_CAS')
    return snapshot

def _runtime_correlation_bridge(self,root,received,snapshot):
    raise Refused('F04_TYPED_INGRESS_ARTIFACT_TERMINAL_BRIDGE_UNAVAILABLE')

def _runtime_stop_exact(self,root,target,ownership):
    require_owned_stop_capability(root,self)
    raise Refused('F04_STOP_API_SCOPE_UNSUPPORTED')

def _runtime_received_custody(self,root,received,bridge):
    ref=received.get('canonical_run');need(reference(ref) and ref['path']==str(STATE/'runs'/(root['run_id']+'.json')),'F04_EXACT_CANONICAL_RUN_REFERENCE_REQUIRED')
    raw=readref(ref);run=json.loads(raw,object_pairs_hook=unique);need(encoded(run)==raw and run.get('id')==root['run_id'] and run.get('scenario_sha256')==root['scenario_ref']['sha256'],'F04_CANONICAL_RECEIVED_RUN_CHANGED')
    docs=[x for x in run.get('observations',[]) if x.get('kind')=='document'];sent=run.get('sent_ids')
    need(type(sent) is list and len(sent)==1 and sent[0]==received.get('sent_message_id') and len(docs)==1,'F04_TESTER_ACK_ARTIFACT_CORRELATION_CHANGED')
    d=docs[0];advertised=d.get('advertised_document',{});artifact=received.get('received_artifact')
    need(type(artifact) is dict and all(artifact.get(k)==d.get(k) for k in ('path','bytes','sha256','message_id','update_id','receipt_path','receipt_sha256','receipt_bytes')) and d.get('complete_artifact') is True and d.get('artifact_acceptance')=='RECEIVED_UNGRADED' and advertised.get('mime_type')=='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and str(advertised.get('file_name','')).lower().endswith('.xlsx') and type(d.get('bytes')) is int and 0<d['bytes']<=1048576,'F04_ACTUAL_RETURNED_XLSX_CHANGED')
    p=Path(d['path']);need(p.is_relative_to(STATE/'downloads'),'F04_CANONICAL_DOWNLOAD_PATH_REQUIRED');readref({'path':str(p),'bytes':d['bytes'],'sha256':d['sha256']});readref({'path':d['receipt_path'],'bytes':d['receipt_bytes'],'sha256':d['receipt_sha256']})
    native_artifact=bridge.get('returned_artifact');joined=type(native_artifact) is dict and native_artifact.get('bytes')==d['bytes'] and native_artifact.get('sha256')==d['sha256'] and native_artifact.get('lease')==bridge['target']['lease'] and reference(native_artifact.get('receipt'))
    if joined:readref(native_artifact['receipt'])
    full180=run.get('status')=='EVIDENCE_READY' and run.get('send_state')=='sent' and run.get('send_attempts')==1 and run.get('repeat_count')==0 and run.get('capture_window_complete') is True and run.get('capture_until')==run.get('sent_at',0)+180 and time.time()>=run.get('capture_until',math.inf) and received.get('full_saved_custody') is True and received.get('full180') is True and received.get('exactly_one_complete_XLSX') is True
    owner=received['ownership'];need(owner.get('run_id')==root['run_id'] and owner.get('operation_id')==root['operation_id'] and type(owner.get('actor')) is dict,'F04_ACTUAL_CONSUMER_OWNERSHIP_CHANGED');actor=owner['actor']
    # An existing reused PID is never signalled and never counted as the owned
    # actor. The caller owns reaping; closure records exact owned actor absence.
    absent=not (Path('/proc')/str(actor.get('pid'))).exists()
    import fcntl
    free=True
    for leaf in ('consumer.lock','tester-token'):
        path=STATE/leaf;need(not any(x.is_symlink() for x in (path,*path.parents)),'F04_POST_CANONICAL_LOCK_LINK');fd=os.open(path,os.O_RDWR|os.O_NOFOLLOW)
        try:
            info=os.fstat(fd);need(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and info.st_nlink==1 and stat.S_IMODE(info.st_mode)==0o600,'F04_POST_CANONICAL_LOCK_CUSTODY')
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:free=False
        finally:os.close(fd)
    need(readref(ref)==raw,'F04_POST_CANONICAL_CAS_CHANGED')
    return dict(full180=full180,actual_artifact_join=joined,actor_absent=absent,canonical_locks_free=free)

RuntimeLeaves.owned_stop_capability=_runtime_owned_stop_capability
RuntimeLeaves.owned_snapshot=_runtime_owned_snapshot
RuntimeLeaves.correlation_bridge=_runtime_correlation_bridge
RuntimeLeaves.stop_exact=_runtime_stop_exact
RuntimeLeaves.received_custody=_runtime_received_custody
