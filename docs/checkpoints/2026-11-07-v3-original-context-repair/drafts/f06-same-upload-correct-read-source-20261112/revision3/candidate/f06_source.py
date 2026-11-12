"""Separate ordinary F06 correct-read SAME upload; original fullv42 consumer.
Import is inert. Actual private scenario/authority/product/current proof are UNBOUND.
No document, credential, Store, API, model or product state is opened on import.
"""
import ast, hashlib, json, re, types
from pathlib import Path
BASE=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py')
BASE_SHA='f0caba28ba9e823574a5149b55989aea7f4e5c893c3a89a7b4eb0ed0cf5e7ad3'
INSTALLED_TESTER=Path('/home/jericho/.local/lib/friday-telegram-bot-test/bot_tester.py')
INSTALLED_TESTER_SHA='cc36c0933bd01cfa5c33a3fb1123fefd0345a2185fbcf7f70f5a3bc2f7c0905b'
PHASE='DOCX-CORRECT-READ-SAME-UPLOAD'
TIMING={'operation_seconds':300,'reply_window_seconds':180,'ack_seconds':10,'reserve_seconds':5,'outer_seconds':600}
PRODUCT_COUNTS={'source_layers':207,'project_files':495,'native_files':17891,'plugin_files':52,'base_source_files':17730}
PRODUCT_COUNTS={k:None for k in PRODUCT_COUNTS}
PRODUCT=dict(PRODUCT_COUNTS,source_receipt_sha256=None,input_sha256=None)
MIME='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
SOURCE={'path':'/home/jericho/.cache/FRW-ASTRA-V3-F06-TYPED-SETTER-FIX-20261112/operations/generate-g6/work/encrypted-inputs/f06-new-encrypted.docx','bytes':23040,'sha256':'22b0dcb3fed3d979b37ff701af42b00d3756d76a863e8f8c736405acc9c33fd5'}
CRYPTO={'container':'CFB','encryption':'OOXML-Standard-3.2','data_integrity_verified':False,'authenticated_MAC':False,'qualification':'password-verifier / ZIP-CRC / readback are not authenticated MAC'}
OBSERVE={'mode':'bounded_reply_capture','window_seconds':180,'max_messages':64,'max_text_chars':8000,'max_documents':0,'document_max_bytes':8*1024**2}
PROOFS={'original_criterion','independent_encrypted_producer','actual_native_qualification','all_profile_history_semantic_once','source_ingress_lineage','private_password_handling','same_B_principal','owned_actor_stop_resources','source_review','authoritative_budget_policy','first_upload_reconciliation','correct_read_private_oracle'}
FIELDS={'schema','status','phase','run_id','scope','scenario_ref','scenario_sha256','authority','authority_id','adapter','footer','actual_root_B_checker','root_current_proof','root_proofs','product','boundary','resources','source','crypto','first_validator','first_ingress','source_reference','installation'}
BOUNDARY={'history_manifest_sha256','cursor_sha256','native_boundary_sha256','once_sha256','ingress_lineage_sha256','gateway','B','phase_unconsumed','uploads_this_operation','producer_calls','restarts'}
def need(v,why):
    if not v:raise ValueError(why)
def encoded(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def digest(v):return hashlib.sha256(v).hexdigest()
def sha(v):return type(v) is str and re.fullmatch('[a-f0-9]{64}',v) is not None
def canonical_path(path):
    text=path if type(path) is str else str(path) if isinstance(path,Path) else None
    need(type(text) is str and text.startswith('/') and not text.startswith('//')
          and not any(ord(ch)<32 or 127<=ord(ch)<=159 for ch in text), 'F06_CANONICAL_ABSOLUTE_PATH_REQUIRED')
    try:text.encode('utf-8')
    except UnicodeError:raise ValueError('F06_CANONICAL_UTF8_PATH_REQUIRED') from None
    need((text=='/' or not any(part in ('','.','..') for part in text.split('/')[1:]))
          and str(Path(text))==text, 'F06_LEXICAL_PATH_ALIAS_REFUSED')
    return Path(text)

def ref(v):return type(v) is dict and set(v)=={'path','bytes','sha256'} and type(v['path']) is str and canonical_path(v['path']).is_absolute() and type(v['bytes']) is int and 0<v['bytes']<=24*1024**2 and sha(v['sha256'])
def readref(v,read):
    need(ref(v),'F06_EXACT_PROTECTED_REFERENCE_REQUIRED');raw=read(canonical_path(v['path']));need(type(raw) is bytes and len(raw)==v['bytes'] and digest(raw)==v['sha256'],'F06_REFERENCE_CHANGED');return raw

def scope():
    return ('Original F-06/P0/LIVE_BOT one separate correct-password READ of SAME actual closed first protected DOCX upload. Text-only ordinary independent operation; max0 uploads/outbound documents, no edits/decrypted copy/new files/password echo/new memory/brute force/producer/restart or old effect replay. First paragraph only, privately assessed against retained independent actual plaintext/structure oracle; generic/refusal/unsupported is not success. Actual first ACK/source_reference/native-ingress/custody/closed reconciliation and fresh Root decision required. No fabricated reply_to/inlinepath, worker continuation, quarantine or second sendDocument. Exact300/full180/ACK10/reserve5/outer600; RECEIVED_UNGRADED/NOT_ESTABLISHED until independent Root grading. Standard3.2 data_integrity_verified=false; password verification/ZIP CRC/readback are not authenticated MAC. Whole F06/170/120/B00 remains open.')


def request_for(supplied_password):
    need(type(supplied_password) is str and bool(supplied_password) and 'UNBOUND' not in supplied_password and not any(ord(c)<32 or 127<=ord(c)<=159 for c in supplied_password),'F06_PRIVATE_CORRECT_PASSWORD_REQUIRED')
    try: units=len(supplied_password.encode('utf-16-le'))//2
    except UnicodeError: raise ValueError('F06_PASSWORD_UTF16_REQUIRED') from None
    need(units<=255,'F06_PASSWORD_UTF16_BOUND')
    return ('В ранее присланном в этой беседе защищённом DOCX f06-new-encrypted.docx используй тестовый пароль «'+supplied_password+'» и прочитай только первый абзац. Не изменяй документ, не создавай расшифрованную копию или новые файлы. Не включай пароль в ответ, не запоминай его отдельно и не подбирай другие пароли.')

def construct_scenario(*,supplied_password,first_dependency):
    # Pure constructor; Root must validate real evidence before any effect.
    need(type(first_dependency) is dict and first_dependency.get('schema')=='frw.Root.F06.closed-first-upload.v1' and first_dependency.get('status')=='ROOT_BOUND_CLOSED_RECONCILED' and first_dependency.get('source',{}).get('sha256')==SOURCE['sha256'] and type(first_dependency.get('source_reference')) is dict,'F06_ACTUAL_FIRST_UPLOAD_REQUIRED')
    return {'tester_id':8812646969,'peer_id':8751854128,'peer_username':'@jerichodevbot','deadline_seconds':300,'max_updates':65,'pace_seconds':1,'steps':[{'request':request_for(supplied_password),'observe':dict(OBSERVE)}]}


def scenario_shape(s):
    need(type(s) is dict and set(s)=={'tester_id','peer_id','peer_username','deadline_seconds','max_updates','pace_seconds','steps'} and type(s['steps']) is list and len(s['steps'])==1,'F06_SINGLETON_CORRECT_READ_REQUIRED')
    need({k:s.get(k) for k in ('tester_id','peer_id','peer_username','deadline_seconds','max_updates','pace_seconds')}=={'tester_id':8812646969,'peer_id':8751854128,'peer_username':'@jerichodevbot','deadline_seconds':300,'max_updates':65,'pace_seconds':1} and all(type(s[k]) is int for k in ('tester_id','peer_id','deadline_seconds','max_updates','pace_seconds')),'F06_EXACT_IDENTITIES_AND_BOUNDS_REQUIRED')
    t=s['steps'][0];need(type(t) is dict and set(t)=={'request','observe'} and t['observe']==OBSERVE and all(type(t['observe'][k]) is int for k in OBSERVE if k!='mode'),'F06_TEXT_ONLY_FULL180_MAX0_REQUIRED')
    p=t['request'];prefix='В ранее присланном в этой беседе защищённом DOCX f06-new-encrypted.docx используй тестовый пароль «';suffix='» и прочитай только первый абзац. Не изменяй документ, не создавай расшифрованную копию или новые файлы. Не включай пароль в ответ, не запоминай его отдельно и не подбирай другие пароли.'
    need(type(p) is str and len(p)<=4000 and p.startswith(prefix) and p.endswith(suffix),'F06_EXACT_CORRECTREAD_REQUEST_REQUIRED')
    need(request_for(p[len(prefix):-len(suffix)])==p,'F06_CORRECTREAD_PRIVATE_CREDENTIAL_REQUIRED');return True


def unbound():
    return {'schema':'frw.F06.same-upload-correctread.v1','status':'UNBOUND_NOT_GRANTED','phase':PHASE,'run_id':'UNBOUND','scope':scope(),'scenario_ref':None,'scenario_sha256':None,'authority':None,'authority_id':'UNBOUND','adapter':None,'footer':None,'actual_root_B_checker':None,'root_current_proof':None,'root_proofs':{k:None for k in sorted(PROOFS)},'product':dict(PRODUCT),'boundary':None,'resources':None,'source':dict(SOURCE),'crypto':dict(CRYPTO),'first_validator':None,'first_ingress':None,'source_reference':None,'installation':None}

def contract_shape(c,*,bound=True):
    need(type(c) is dict and set(c)==FIELDS and c['schema']=='frw.F06.same-upload-correctread.v1' and c['phase']==PHASE and c['scope']==scope() and c['source']==SOURCE and c['crypto']==CRYPTO,'F06_EXACT_CORRECT_READ_CONTRACT_REQUIRED')
    p=c['product'];need(type(p) is dict and set(p)==set(PRODUCT) and (all(p[k] is None for k in PRODUCT_COUNTS) if not bound and all(p[k] is None for k in PRODUCT_COUNTS) else all(type(p[k]) is int and p[k]>0 for k in PRODUCT_COUNTS)),'F06_ACTUAL_ROOT_PRODUCT_TUPLE_REQUIRED')
    if not bound:return True
    need(c['status']=='ROOT_BOUND_EXACT_F06_CORRECTREAD' and all(sha(p[k]) for k in ('source_receipt_sha256','input_sha256')),'F06_ROOT_ACTUAL_PRODUCT_UNBOUND')
    need(type(c['run_id']) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',c['run_id']) is not None and c['run_id']!='UNBOUND' and type(c['authority_id']) is str and bool(c['authority_id']) and c['authority_id']!='UNBOUND' and sha(c['scenario_sha256']),'F06_EXACT_PRIVATE_SCENARIO_AUTHORITY_REQUIRED')
    need(all(ref(c[k]) for k in ('scenario_ref','authority','adapter','footer','actual_root_B_checker','root_current_proof','first_validator','first_ingress')) and type(c['root_proofs']) is dict and set(c['root_proofs'])==PROOFS and all(ref(v) for v in c['root_proofs'].values()),'F06_ACTUAL_ROOT_PROOFS_UNBOUND')
    b=c['boundary'];need(type(b) is dict and set(b)==BOUNDARY and all(sha(b[k]) for k in BOUNDARY-{'gateway','B','phase_unconsumed','uploads_this_operation','producer_calls','restarts'}) and b['phase_unconsumed'] is True and type(b['uploads_this_operation']) is int and b['uploads_this_operation']==0 and type(b['producer_calls']) is int and b['producer_calls']==0 and type(b['restarts']) is int and b['restarts']==0,'F06_ZERO_UPLOAD_CORRECTREAD_ONCE_UNBOUND')
    need(type(b['gateway']) is dict and type(b['B']) is dict and b['B'].get('profile')=='telegram-bot-8812646969' and type(b['B'].get('session_id')) is str and b['B']['session_id'] and type(b['B'].get('session_key')) is str and b['B']['session_key'] and type(b['B'].get('native_max_id')) is int and b['B']['native_max_id']>=0,'F06_SAME_B_SESSION_UNBOUND')
    need(type(c['installation']) is dict and set(c['installation'])=={'closure','source_acceptance','product','runtime_hashes'} and c['installation']['product']==p and ref(c['installation']['closure']) and ref(c['installation']['source_acceptance']) and type(c['installation']['runtime_hashes']) is dict and c['installation']['runtime_hashes'],'F06_ROOT_INSTALLATION_BINDING_REQUIRED')
    need(type(c['source_reference']) is dict and set(c['source_reference'])=={'run_id','run_sha256','input_sha256'} and c['source_reference']['input_sha256']==SOURCE['sha256'] and sha(c['source_reference']['run_sha256']) and c['source_reference']['run_id']!=c['run_id'],'F06_FIRST_SOURCE_REF_REQUIRED')
    r=c['resources'];need(type(r) is dict and set(r)==set(TIMING)|{'cpu_seconds','max_rss_bytes','disk_bytes','clock','owned_parent_wait_cleanup'} and all(type(r[k]) is int and r[k]==v for k,v in TIMING.items()) and type(r['cpu_seconds']) is int and r['cpu_seconds']>0 and type(r['max_rss_bytes']) is int and 0<r['max_rss_bytes']<=2*1024**3 and type(r['disk_bytes']) is int and 0<r['disk_bytes']<=64*1024**2 and ref(r['clock']) and ref(r['owned_parent_wait_cleanup']),'F06_FINITE_ACTUAL_CONSUMER_RESOURCES_UNBOUND');return True

def shape(c,name,s,read):
    contract_shape(c);scenario_shape(s)
    validate_first(c,read)
    need(name==c['run_id'] and digest(encoded(s))==c['scenario_sha256'] and c['scenario_ref']['sha256']==c['scenario_sha256'] and readref(c['scenario_ref'],read)==encoded(s),'F06_EXACT_PRIVATE_SCENARIO_CHANGED');return True

def admission(c,d):
    contract_shape(c)
    need(type(d) is dict and d.get('authority_id')==c['authority_id'] and d.get('scope')==c['scope'] and d.get('run_scenarios')=={c['run_id']:c['scenario_sha256']} and d.get('ordered_predecessors',{})=={} and d.get('same_canonical_local_run') is False and 'memory_case' not in d,'F06_SINGLETON_ORDINARY_AUTHORITY_NO_MEMORY_GRANT');return True

def effect(c):
    """Exact whole effect incl scenario/credentials hash and source/gates/resources.
    Issued authority and current proof are checked separately; excluding them avoids
    a hash cycle. No capture words/request markers can authorize this operation.
    """
    return {k:c[k] for k in sorted(FIELDS-{'authority','authority_id','root_current_proof','status'})}

def current_gate(c,phase,state,state_raw,state_path,read):
    contract_shape(c);need(phase in ('NEW','CURSOR_AUTHORITY','PRE_INTENT_REVALIDATION'),'F06_PRE_INTENT_GATE_ONLY')
    raw=readref(c['actual_root_B_checker'],read);m=types.ModuleType('_actual_F06_Root_B_checker');m.__file__=c['actual_root_B_checker']['path'];exec(compile(raw,m.__file__,'exec'),m.__dict__)
    readref(c['root_current_proof'],read)
    for item in c['root_proofs'].values():readref(item,read)
    f=m.check(c['root_current_proof']['path'],c['root_current_proof']['sha256'])
    need(type(f) is dict and f.get('admission') is False and f.get('installed_product')==c['product'] and f.get('Root_proof_sha256')==c['root_current_proof']['sha256'] and f.get('f06_mutable_boundary')==c['boundary'] and f.get('whole_effect_sha256')==digest(encoded(effect(c))),'F06_ROOT_B_CURRENT_BOUNDARY_CHANGED')
    need(f.get('gateway')==c['boundary']['gateway'] and f['gateway'].get('pid')==state.get('pid') and f['gateway'].get('start_time')==state.get('start_time') and read(state_path,private=False)==state_raw,'F06_GATEWAY_CHANGED')
    n=f.get('native_readonly',{});b=c['boundary']['B'];need(n.get('read_only') is True and n.get('quiescent') is True and n.get('session_id')==b['session_id'] and n.get('session_key')==b['session_key'] and n.get('identity')==f['gateway'],'F06_FRESH_B_NATIVE_CESSATION_REQUIRED');return True

def successor(base_raw,c,footer_raw):
    """Same original fullv42; three existing AST pins, currentRoot callsite/footer.
    Core refusal capture, ingress, once, sender, stop, custody/window are unchanged.
    """
    need(type(base_raw) is bytes and digest(base_raw)==BASE_SHA,'F06_EXACT_FULL_V42_REQUIRED');contract_shape(c,bound=False)
    text=base_raw.decode();tree=ast.parse(text);runner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Runner');lines=text.splitlines(keepends=True);changes=[]
    for name,value in [('ORDINARY_INDEPENDENT_SCENARIOS',{c['run_id']:c['scenario_sha256']}),('ORDINARY_INDEPENDENT_AUTHORITY',c['authority'])]:
        n=next(n for n in runner.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets));changes.append((n.lineno,n.end_lineno,'    '+name+' = '+repr(value)+'\n'))
    method=next(n for n in runner.body if isinstance(n,ast.FunctionDef) and n.name=='ordinary_independent_admission');ids=[n for n in ast.walk(method) if isinstance(n,ast.Constant) and n.value=='ordinary-independent-jarvis-activate-20261109-r68'];need(len(ids)==1,'F06_AUTHORITY_ID_SEAM_REQUIRED');n=ids[0];changes.append((n.lineno,n.end_lineno,lines[n.lineno-1][:n.col_offset]+repr(c['authority_id'])+lines[n.lineno-1][n.end_col_offset:]))
    for lo,hi,new in sorted(changes,reverse=True):lines[lo-1:hi]=[new]
    text=''.join(lines);old="or not 0 <= now - updated <= gateway['maximum_staleness_seconds']";need(text.count(old)==1,'F06_FRESHNESS_SEAM_REQUIRED');text=text.replace(old,'or not _f06_current(state,state_raw,state_path)')
    need(type(footer_raw) is bytes,'F06_FOOTER_BYTES_REQUIRED')
    if c['status']!='UNBOUND_NOT_GRANTED':need(ref(c['footer']) and len(footer_raw)==c['footer']['bytes'] and digest(footer_raw)==c['footer']['sha256'],'F06_PINNED_FOOTER_REQUIRED')
    footer=footer_raw.decode();need(footer.count('__CONTRACT__')==1,'F06_EXACT_FOOTER_REQUIRED');main="if __name__ == '__main__':\n    sys.exit(main())";need(text.count(main)==1,'F06_MAIN_SEAM_REQUIRED');text=text.replace(main,footer.replace('__CONTRACT__',repr(c))+'\n'+main);ast.parse(text);return text.encode()


def validate_first(c,read):
    raw=readref(c['first_validator'],read)
    m=types.ModuleType('_F06_exact_first_ingress');m.__file__=c['first_validator']['path']
    exec(compile(raw,m.__file__,'exec'),m.__dict__)
    first=m.validate(c,read)
    m.private_oracle(c,read)
    return first
