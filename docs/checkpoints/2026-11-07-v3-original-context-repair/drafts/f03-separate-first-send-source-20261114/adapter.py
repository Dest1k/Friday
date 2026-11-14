"""F03 original ODS/formulas singleton adapter over unchanged full v42.
SOURCE ONLY. Inert import; no current observation, proof, grant or effects.
Root supplies exact current stat/scenario/frontier. First ingress is a future
postcondition of one admitted upload; it is never required before that upload.
"""
import ast, copy, hashlib, json, math, os, re, types
from pathlib import Path
BASE=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py')
BASE_SHA='f0caba28ba9e823574a5149b55989aea7f4e5c893c3a89a7b4eb0ed0cf5e7ad3'
RUN_ID='f03-ods-formulas-original-221-20261114'
CASE='F-03'; OPERATION='CASE164/format27/edit/formulas-v02/row667'; PHASE='FIRST-ORDINARY-UPLOAD-EDIT-RETURN'
SID='20261030_093055_43bba39f';KEY='agent:telegram-bot-8812646969:telegram:dm:8812646969'
SOURCE={'path':'/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114/input/orders-formulas-original.ods','bytes':16538,'sha256':'a2e68bc685e4d689aa7972ff4f2c7f9841441c9dcb4fc5e40327a5ae190b5d58'}
PROPOSAL={'path':'/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114/SCENARIO-PROPOSAL.private.json','bytes':2191,'sha256':'c62fa2c1155f12219b94a383342e18023c87f3f03ba5b3db1c9af7a7a46c5a5b'}
PROPOSAL_CANONICAL_SHA='64fcfb32516b95e1169c2102414c5f2ef2f7eb2551e95f6ed91ee5442a2eb6ce'
EXPECTED={'source_layers':221,'project_files':523,'native_files':17893,'plugin_files':52,'base_source_files':17730,'source_receipt_sha256':'a4d278c67b044b684c3182107947bdb9d82a592b54924d9a5bb283fc11ac1d40','input_sha256':'60d879571771e861df8441a02489cb74bf8d8707e2f14e0ae3448b81ed87504d'}
TIMING={'operation_seconds':300,'reply_window_seconds':180,'ack_seconds':30,'reserve_seconds':5,'outer_seconds':600}
INPUT_STAT_FIELDS={'device','inode','size_bytes','uid','mtime_ns','ctime_ns'}
PROOFS={'original_selection','source_custody','all_profile_history_semantic_once','private_exclusion','source_review','owned_actor_stop_resources'}
FIELDS={'schema','status','case','operation_id','phase','run_id','scope','scenario_ref','scenario_sha256','source','proposal_ref','expected_product','adapter','current_gate','root_current_review','root_proofs','mutable_boundary','resources'}
SCOPE=('One genuinely missing original CASE164/F-03 format27 ODS edit formulas/v02 row667: '
       'Orders C2 numeric 2 to 3 in exact retained rich ODS. One ordinary document upload '
       'and new same-format returned copy in existing tester8812646969 peer8751854128 conversation; '
       'source unchanged; all sheets/formulas/text IDs/relevant existing structure preserved, '
       'honest cache/coverage disclosure. First ordinary ingress/delivery/custody are runtime '
       'postconditions, never invented preconditions. Root positive original/frontier/current '
       'source/principal/ACL/history/private exclusion/once required. Original300/full180/ACK30/'
       'reserve5/outer600; max1 captured document<=1MiB,max4 messages,text8000. No new producer, '
       'Office, install, restart, old R86/S11 replay, source110 UNKNOWN clearance, automatic '
       'followup or semantic acceptance. NOT a B00 acceptance; NOT a product acceptance.')

def require(ok,why):
    if not ok:raise ValueError(why)
def encoded(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def sha(v):return type(v) is str and re.fullmatch('[a-f0-9]{64}',v) is not None
def reference(v):
    return type(v) is dict and set(v)=={'path','bytes','sha256'} and type(v['path']) is str and Path(v['path']).is_absolute() and str(Path(v['path']))==v['path'] and not any(q in ('','.','..') for q in v['path'].split('/')[1:]) and type(v['bytes']) is int and 0<v['bytes']<=24*1024**2 and sha(v['sha256'])
def load_reference(r,read,*,private=True):
    require(reference(r),'F03_EXACT_PROTECTED_REFERENCE_REQUIRED');raw=read(Path(r['path']),private=private)
    require(type(raw) is bytes and len(raw)==r['bytes'] and digest(raw)==r['sha256'],'F03_PIN_CHANGED');return raw
def stat_shape(pin):
    require(type(pin) is dict and set(pin)==INPUT_STAT_FIELDS and all(type(pin[k]) is int and pin[k]>=0 for k in pin) and pin['uid']==os.getuid() and pin['inode']>0 and pin['size_bytes']==SOURCE['bytes'],'F03_FRESH_EXACT_SOURCE_STAT_REQUIRED');return True

def construct_scenario(proposal,source_stat):
    """Pure constructor. stat is supplied by Root; no permission or current claim."""
    require(type(proposal) is dict and digest(encoded(proposal))==PROPOSAL_CANONICAL_SHA,'F03_EXACT_IMMUTABLE_PROPOSAL_REQUIRED');stat_shape(source_stat)
    result=copy.deepcopy(proposal);require('stat' not in result['steps'][0]['input'],'F03_PROPOSAL_ALREADY_MUTATED')
    result['steps'][0]['input']['stat']=dict(source_stat);return result

def scenario_shape(s):
    require(type(s) is dict and set(s)=={'tester_id','peer_id','peer_username','deadline_seconds','max_updates','pace_seconds','steps'} and type(s['steps']) is list and len(s['steps'])==1,'F03_EXACT_SINGLETON_REQUIRED')
    step=s['steps'][0];require(type(step) is dict and set(step)=={'input','observe'} and type(step['input']) is dict,'F03_ORDINARY_DOCUMENT_INPUT_REQUIRED')
    pin=step['input'].get('stat');stat_shape(pin)
    proposal=copy.deepcopy(s);del proposal['steps'][0]['input']['stat']
    require(digest(encoded(proposal))==PROPOSAL_CANONICAL_SHA,'F03_ORIGINAL_REQUEST_SOURCE_OR_BOUNDS_CHANGED');return True

def unbound():
    return dict(schema='frw.F03.original-ordinary221.binding.v1',status='UNBOUND_NOT_GRANTED',case=CASE,operation_id=OPERATION,phase=PHASE,run_id=RUN_ID,scope=SCOPE,scenario_ref=None,scenario_sha256=None,source=dict(SOURCE),proposal_ref=dict(PROPOSAL),expected_product=dict(EXPECTED),adapter=None,current_gate=None,root_current_review=None,root_proofs={k:None for k in sorted(PROOFS)},mutable_boundary=None,resources=None)

def contract_shape(c,*,bound=True):
    require(type(c) is dict and set(c)==FIELDS and c['schema']=='frw.F03.original-ordinary221.binding.v1' and c['case']==CASE and c['operation_id']==OPERATION and c['phase']==PHASE and c['run_id']==RUN_ID and c['scope']==SCOPE and c['source']==SOURCE and c['proposal_ref']==PROPOSAL and c['expected_product']==EXPECTED,'F03_EXACT_ORIGINAL_BINDING_REQUIRED')
    if not bound:return True
    require(c['status']=='ROOT_BOUND_EXACT_F03','F03_UNBOUND_NO_DISPATCH')
    require(all(reference(c[k]) for k in ('scenario_ref','adapter','current_gate','root_current_review')) and sha(c['scenario_sha256']) and c['scenario_ref']['sha256']==c['scenario_sha256'],'F03_ACTUAL_SCENARIO_AND_CURRENT_REFS_UNBOUND')
    require(type(c['root_proofs']) is dict and set(c['root_proofs'])==PROOFS and all(reference(v) for v in c['root_proofs'].values()),'F03_ROOT_PRECONDITIONS_UNBOUND')
    require(type(c['mutable_boundary']) is dict and c['mutable_boundary'],'F03_CURRENT_MUTABLE_BOUNDARY_UNBOUND')
    r=c['resources'];require(type(r) is dict and set(r)==set(TIMING)|{'cpu_seconds','max_rss_bytes','disk_bytes','clock'} and all(type(r[k]) is int and r[k]==v for k,v in TIMING.items()) and type(r['cpu_seconds']) is int and r['cpu_seconds']>0 and type(r['max_rss_bytes']) is int and 0<r['max_rss_bytes']<=2*1024**3 and type(r['disk_bytes']) is int and 0<r['disk_bytes']<=64*1024**2 and reference(r['clock']),'F03_ORIGINAL_FINITE_RESOURCES_UNBOUND');return True

def shape(c,name,s,read):
    contract_shape(c);scenario_shape(s)
    require(name==RUN_ID and encoded(s)==load_reference(c['scenario_ref'],read) and digest(encoded(s))==c['scenario_sha256'],'F03_CANONICAL_SCENARIO_CHANGED')
    require(digest(encoded(json.loads(load_reference(PROPOSAL,read))))==PROPOSAL_CANONICAL_SHA,'F03_PROPOSAL_CONTENT_CHANGED')
    raw=load_reference(SOURCE,read)
    info=Path(SOURCE['path']).stat();actual={k:getattr(info,'st_'+{'device':'dev','inode':'ino','size_bytes':'size'}.get(k,k)) for k in INPUT_STAT_FIELDS}
    require(actual==s['steps'][0]['input']['stat'],'F03_CURRENT_SOURCE_STAT_CHANGED');return True

def effect(c):return {k:c[k] for k in sorted(FIELDS-{'status','root_current_review'})}
def admission(c,name,s,d,read):
    shape(c,name,s,read)
    require(type(d) is dict and d.get('scope')==SCOPE and d.get('run_scenarios')=={RUN_ID:c['scenario_sha256']} and d.get('ordered_predecessors',{})=={} and d.get('same_canonical_local_run') is False and 'memory_case' not in d,'F03_EXACT_SINGLETON_AUTHORITY_REQUIRED');return True

def current_gate(c,phase,state,state_raw,state_path,read,*,first_send=None):
    contract_shape(c);require(phase in ('NEW','CURSOR_AUTHORITY','PRE_INTENT_REVALIDATION'),'F03_PRE_INTENT_GATE_ONLY')
    raw=load_reference(c['current_gate'],read);m=types.ModuleType('_F03_exact_current221');m.__file__=c['current_gate']['path'];exec(compile(raw,m.__file__,'exec'),m.__dict__)
    m.readref(c['root_current_review'])
    for item in c['root_proofs'].values():load_reference(item,read)
    f=m.check(c['root_current_review']['path'],c['root_current_review']['sha256'],boundary_phase=phase,first_send=first_send)
    require(type(f) is dict and f.get('admission') is False and f.get('installed_product')==EXPECTED and f.get('Root_proof_sha256')==c['root_current_review']['sha256'] and f.get('f03_mutable_boundary')==c['mutable_boundary'] and f.get('whole_effect_sha256')==digest(encoded(effect(c))),'F03_CURRENT_SOURCE_PROFILE_PRIVATE_HISTORY_ONCE_CHANGED')
    gateway=f.get('gateway',{});require(gateway.get('pid')==state.get('pid') and gateway.get('start_time')==state.get('start_time') and read(state_path,private=False)==state_raw,'F03_CURRENT_GATEWAY_CAS_CHANGED')
    n=f.get('native_readonly',{});require(n.get('read_only') is True and n.get('quiescent') is True and n.get('session_id')==SID and n.get('session_key')==KEY and n.get('identity')==gateway,'F03_ACTUAL_SAME_PRINCIPAL_NATIVE_REQUIRED');return True

def successor(base_raw,authority,authority_id,c,footer_raw):
    """Existing M14 seams only plus exact F03 footer's scoped ACK30 wrapper.
    Full v42 sender/capture/locks/once/CAS/window/custody/stop remain unchanged.
    """
    require(type(base_raw) is bytes and digest(base_raw)==BASE_SHA,'F03_FULL_V42_SOURCE_REQUIRED');contract_shape(c,bound=False)
    require(reference(authority) and type(authority_id) is str and authority_id and authority_id!='UNBOUND','F03_FUTURE_EXACT_AUTHORITY_REQUIRED')
    text=base_raw.decode();tree=ast.parse(text);runner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Runner');lines=text.splitlines(keepends=True);changes=[]
    for name,value in [('ORDINARY_INDEPENDENT_SCENARIOS',{RUN_ID:c['scenario_sha256']}),('ORDINARY_INDEPENDENT_AUTHORITY',authority)]:
        n=next(n for n in runner.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets));changes.append((n.lineno,n.end_lineno,'    '+name+' = '+repr(json.loads(encoded(value)))+'\n'))
    method=next(n for n in runner.body if isinstance(n,ast.FunctionDef) and n.name=='ordinary_independent_admission');ids=[n for n in ast.walk(method) if isinstance(n,ast.Constant) and n.value=='ordinary-independent-jarvis-activate-20261109-r68'];require(len(ids)==1,'F03_AUTHORITY_ID_SEAM_REQUIRED');n=ids[0];changes.append((n.lineno,n.end_lineno,lines[n.lineno-1][:n.col_offset]+repr(authority_id)+lines[n.lineno-1][n.end_col_offset:]))
    for lo,hi,new in sorted(changes,reverse=True):lines[lo-1:hi]=[new]
    text=''.join(lines);old="or not 0 <= now - updated <= gateway['maximum_staleness_seconds']";require(text.count(old)==1,'F03_CURRENT_GATE_SEAM_REQUIRED');text=text.replace(old,'or not _f03_native_freshness(state,state_raw,state_path)')
    require(type(footer_raw) is bytes and footer_raw.count(b'__CONTRACT__')==1,'F03_EXACT_FOOTER_REQUIRED')
    main="if __name__ == '__main__':\n    sys.exit(main())";require(text.count(main)==1,'F03_MAIN_SEAM_REQUIRED');text=text.replace(main,footer_raw.decode().replace('__CONTRACT__',repr(json.loads(encoded(c))))+'\n'+main);ast.parse(text);return text.encode()
