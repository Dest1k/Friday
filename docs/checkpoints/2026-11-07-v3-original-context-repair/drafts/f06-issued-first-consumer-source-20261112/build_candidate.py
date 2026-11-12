"""Source-only adaptation. Reads source and explicitly permitted Root closure metadata."""
import hashlib,json,os,types
from pathlib import Path
os.umask(0o077)
U=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ORDINARY207-ROOT-BINDING-SOURCE-20261112')
W=Path(__file__).resolve().parent
O=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-FIRST-ORDINARY-WRONGREAD-20261112/PREBIRTH-ISSUER-ONLY-CLOSURE.json')
O_SHA='d8f6c472ab34a1349e8dfb49ead0a95383aa479728c8d0fa818a4446b12a83f5'
def save(name,raw):
 p=W/name;p.write_bytes(raw);p.chmod(0o600)
def replace(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
raw=O.read_bytes();assert hashlib.sha256(raw).hexdigest()==O_SHA
save('ROOT-PREBIRTH-CLOSURE.METADATA.json',raw)
s=(U/'f06_source.py').read_text()
s=replace(s,'import ast, hashlib, json, re, types','import ast, hashlib, json, math, re, time, types')
s=replace(s,"'authority','authority_id','adapter'","'authority','authority_id','authority_chain','adapter'")
s=replace(s,"'authority_id':'UNBOUND','adapter'","'authority_id':'UNBOUND','authority_chain':None,'adapter'")
s=replace(s,"type(c['authority_id']) is str and c['authority_id'].startswith('ordinary-independent-')","opaque_identity(c['authority_id'])")
s=replace(s,'def contract_shape(c,*,bound=True):', '''def opaque_identity(value):
    # Issuer labels are opaque identities. Prefixes never grant permission.
    return type(value) is str and 1<=len(value)<=256 and value!='UNBOUND' and all(32<ord(ch)<127 for ch in value)

def contract_shape(c,*,bound=True):''')
s=replace(s,"    b=c['boundary'];need", "    chain=c['authority_chain'];need(type(chain) is dict and set(chain)=={'predecessor','predecessor_authority_id','created_at','expires_at'} and ref(chain['predecessor']) and opaque_identity(chain['predecessor_authority_id']) and chain['predecessor_authority_id']!=c['authority_id'] and all(type(chain[k]) in (int,float) and math.isfinite(chain[k]) for k in ('created_at','expires_at')) and 0<=chain['created_at']<chain['expires_at']<=chain['created_at']+6*3600,'F06_EXACT_EXISTING_ISSUANCE_CHAIN_REQUIRED')\n    b=c['boundary'];need")
start=s.index('def admission(c,d):');end=s.index('\ndef effect(c):',start)
s=s[:start]+'''def admission(c,d,*,read,now=None):
    """Validate exact released bytes and immediate released chain, never an ID label."""
    contract_shape(c)
    raw=readref(c['authority'],read)
    need(type(d) is dict and encoded(d)==raw,'F06_EXACT_CANONICAL_ISSUED_BYTES_REQUIRED')
    chain=c['authority_chain'];parent=json.loads(readref(chain['predecessor'],read))
    need(type(parent) is dict and parent.get('schema')=='frw.Root.ordinary-independent-history-admission.v1' and parent.get('accepted') is True and parent.get('authority_id')==chain['predecessor_authority_id'],'F06_EXACT_RELEASED_PREDECESSOR_REQUIRED')
    supersedes=d.get('supersedes')
    need(type(supersedes) is dict and set(supersedes)=={'authority_id','reason'} and supersedes['authority_id']==chain['predecessor_authority_id'] and type(supersedes['reason']) is str and supersedes['reason'].strip(),'F06_ISSUED_SUPERSEDES_CHAIN_MISMATCH')
    now=time.time() if now is None else now
    need(type(now) in (int,float) and math.isfinite(now) and d.get('created_at')==chain['created_at'] and d.get('expires_at')==chain['expires_at'] and chain['created_at']<=now<chain['expires_at'],'F06_EXISTING_AUTHORITY_EXPIRED_OR_TIMES_CHANGED')
    need(d.get('schema')=='frw.Root.ordinary-independent-history-admission.v1' and d.get('operator')=='Root' and d.get('accepted') is True and d.get('authority_id')==c['authority_id'] and d.get('scope')==c['scope'] and d.get('run_scenarios')=={c['run_id']:c['scenario_sha256']} and d.get('ordered_predecessors',{})=={} and d.get('same_canonical_local_run') is False and 'memory_case' not in d,'F06_SINGLETON_ORDINARY_AUTHORITY_NO_MEMORY_GRANT');return True
''' +s[end:]
save('f06_source.py',s.encode())
s=(U/'f06_footer.py.txt').read_text()
s=replace(s,"_m.admission(F06_CONTRACT,json.loads(safe_read(_f06_path(self.ORDINARY_INDEPENDENT_AUTHORITY['path'])),object_pairs_hook=unique_object))","_m.admission(F06_CONTRACT,json.loads(safe_read(_f06_path(self.ORDINARY_INDEPENDENT_AUTHORITY['path'])),object_pairs_hook=unique_object),read=safe_read)")
s=replace(s,'_m.admission(F06_CONTRACT,_document)','_m.admission(F06_CONTRACT,_document,read=safe_read)')
save('f06_footer.py.txt',s.encode())
s=(U/'current207.py').read_text()
s=replace(s,"    materials += [str(canonical_path(c['resources'][k]['path']).parent) for k in ('clock','owned_parent_wait_cleanup')]","    materials += [str(canonical_path(c['resources'][k]['path']).parent) for k in ('clock','owned_parent_wait_cleanup')]\n    materials += [str(canonical_path(c['authority_chain']['predecessor']['path']).parent)]")
save('current207.py',s.encode())
s=(U/'root_bind_dispatch_once.py').read_text()
s=replace(s,'"""Root-owned finite firstF06 issuer/binder/full-consumer caller. Import is inert.', '"""Root-owned first-consumer-only caller for an already issued R106. Import is inert.')
s=replace(s,'contextlib, datetime as dt, fcntl, hashlib, io, json','datetime as dt, fcntl, hashlib, json')
start=s.index('ISSUER=');end=s.index("PYTHON=",start)
s=s[:start]+'''ORIGINAL_DIR=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-FIRST-ORDINARY-WRONGREAD-20261112')
PREBIRTH_CLOSURE={'path':str(ORIGINAL_DIR/'PREBIRTH-ISSUER-ONLY-CLOSURE.json'),'bytes':None,'sha256':'d8f6c472ab34a1349e8dfb49ead0a95383aa479728c8d0fa818a4446b12a83f5'}
EXISTING_AUTHORITY={'path':'/home/jericho/.cache/FRW-KIMI-FMT-20261108/INDEPENDENT-AUTHORITY-R106.json','bytes':14157,'sha256':'3dac8de65e8cd1e7ccb612b5eddccbed12bc256b8e67e56fd280b7d8d12d97ec'}
EXISTING_AUTHORITY_ID='ordinary-f04-postfix-diagnostic-20261112-r106'
EXISTING_CREATED=1794457434.732844
EXISTING_EXPIRES=1794479034.732844
ORIGINAL_RUN='f06-first-docx-wrong-read-20261112-r1'
ORIGINAL_SCENARIO_SHA='91e3c83b52337b7b62349533354cab88486f2ba3a7f946f58059b52bcecb75b3'
''' + s[end:]
# Closure byte count is explicit source metadata, never a dynamically relabeled pin.
s=s.replace("'bytes':None,'sha256':'d8f6", "'bytes':"+str(len(raw))+",'sha256':'d8f6")
start=s.index('def validate_inputs(v):');end=s.index('\ndef clock_remaining',start)
s=s[:start]+'''def validate_inputs(v):
    need(type(v) is dict and set(v)=={'schema','status','contract','source_freeze','independent_review','workdir','slot_identity','expected_binding_sha256','prebirth_closure','prebirth_reconciliation'} and v['schema']=='frw.Root.F06.existing-R106-first-consumer.v1' and v['status']=='ROOT_BOUND_SEPARATE_UNSTARTED_CONSUMER','F06_CONSUMER_STAGE_UNBOUND_NO_EFFECT')
    c=v['contract']
    need(type(c) is dict and c.get('authority')==EXISTING_AUTHORITY and c.get('authority_id')==EXISTING_AUTHORITY_ID and c.get('status')=='ROOT_BOUND_EXACT_F06_FIRST_WRONGREAD' and c.get('run_id')==ORIGINAL_RUN and c.get('scenario_sha256')==ORIGINAL_SCENARIO_SHA and c.get('scenario_ref',{}).get('sha256')==ORIGINAL_SCENARIO_SHA,'F06_ONLY_ORIGINAL_RUN_AND_EXISTING_R106')
    need(c.get('authority_chain',{}).get('created_at')==EXISTING_CREATED and c['authority_chain'].get('expires_at')==EXISTING_EXPIRES and v['prebirth_closure']==PREBIRTH_CLOSURE,'F06_EXISTING_ISSUANCE_OR_CLOSURE_CHANGED')
    need(type(v['workdir']) is str and canonical_path(v['workdir']).is_absolute() and v['expected_binding_sha256'] is None,'F06_FRESH_CONSUMER_BINDING_REQUIRED')
    work=canonical_path(v['workdir'])
    need(not work.is_relative_to(ORIGINAL_DIR) and not ORIGINAL_DIR.is_relative_to(work),'F06_OLD_DRIVER_WORKDIR_MUST_REMAIN_UNTOUCHED')
    return True

def prebirth_reconciled(v):
    """Read-only pins and Root judgement for the separately admitted missing stage.
    Old driver/issuance/once/600 are closed historical effects, never resumed.
    """
    closure=json.loads(readref(v['prebirth_closure']),object_pairs_hook=unique)
    need(closure.get('schema')=='friday.root.F06.first-driver-prebirth-refusal-closure.v1' and closure.get('state')=='DRIVER_CLOSED_AFTER_ISSUANCE_BEFORE_BIND_OR_CONSUMER_BIRTH_NO_SEND' and closure.get('actual_issued_authority')==EXISTING_AUTHORITY and closure.get('actual_authority_id')==EXISTING_AUTHORITY_ID and closure.get('consumer_birth') is False and closure.get('dispatch_invocation_absent') is True and closure.get('canonical_run_absent') is True and closure.get('no_API_client_created') is True and closure.get('reissue_retry_resume_or_rename_authorized') is False,'F06_GENUINE_ISSUER_ONLY_PREBIRTH_CLOSURE_REQUIRED')
    oldonce=closure['once_claim_preserved'];oldclock=closure['original_clock']
    once=json.loads(readref(oldonce),object_pairs_hook=unique)
    clock=json.loads(readref(oldclock),object_pairs_hook=unique)
    need(oldonce['path']==str(ORIGINAL_DIR/'work/ROOT-ONCE-INVOCATION.json') and oldclock['path']==str(ORIGINAL_DIR/'EXECUTION-CLOCK.json') and once.get('schema')=='frw.Root.F06.one-driver-invocation.v1' and once.get('run_id')==ORIGINAL_RUN and once.get('no_retry') is True and clock==closure['original_clock_endpoints_preserved'],'F06_OLD_ONCE_OR_CLOCK_ERASED_RENAMED_OR_CHANGED')
    need(not (Path('/proc')/str(closure['actual_root_driver_pid'])).exists(),'F06_OLD_ROOT_DRIVER_STILL_PRESENT')
    for name in ('ROOT-ACTUAL-BINDING.json','bot_tester.f06.root-bound.py','ROOT-DISPATCH-INVOCATION.json','ROOT-CONSUMER-ACTOR.json','ROOT-STOP-UNCONFIRMED.json','ROOT-DISPATCH-ENDED.json','CONSUMER.stdout','CONSUMER.stderr'):
        need(not os.path.lexists(ORIGINAL_DIR/'work'/name),'F06_PRIOR_CONSUMER_BIND_DISPATCH_BIRTH_OR_UNKNOWN')
    need(not os.path.lexists(STATE/'runs'/(ORIGINAL_RUN+'.json')),'F06_PRIOR_CANONICAL_RUN_REFUSE')
    r=json.loads(readref(v['prebirth_reconciliation']),object_pairs_hook=unique)
    need(r.get('schema')=='frw.Root.F06.issuer-only-prebirth-reconciliation.v1' and r.get('operator')=='Root' and r.get('status')=='ROOT_BOUND_SEPARATELY_ADMITTED_UNSTARTED_CONSUMER' and r.get('prebirth_closure')==v['prebirth_closure'] and r.get('original_run_id')==ORIGINAL_RUN and r.get('scenario_sha256')==ORIGINAL_SCENARIO_SHA and r.get('existing_authority')==EXISTING_AUTHORITY and r.get('old_once')==oldonce and r.get('old_clock')==oldclock,'F06_ROOT_RECONCILIATION_EXACT_REFS_REQUIRED')
    for key in ('first_consumer_stage_never_started','old_driver_closed_and_absent','old_once_and_clock_preserved','no_prior_bind_dispatch_canonicalrun_or_unknown','existing_issuance_scope_run_hash_chain_accepted','separate_missing_segment_authorized','no_old_driver_or_issuer_retry'):
        need(r.get(key) is True,'F06_ROOT_PREBIRTH_RECONCILIATION_REQUIRED')
    need(type(r.get('created_at')) in (int,float) and type(r.get('expires_at')) in (int,float) and math.isfinite(r['created_at']) and math.isfinite(r['expires_at']) and r['created_at']<=time.time()<r['expires_at']<=r['created_at']+120,'F06_ROOT_PREBIRTH_RECONCILIATION_STALE')
    need(v['contract']['resources']['clock']!=oldclock and v['contract']['resources']['clock']['path']!=oldclock['path'],'F06_OLD_CLOCK_REUSE_OR_EXTENSION_REFUSED')
    return closure
''' +s[end:]
s=s.replace('frw.Root.F06.original-finite-clock.v1','frw.Root.F06.unstarted-consumer-finite-clock.v1')
s=s.replace('F06_EXACT_ORIGINAL_CLOCK_REQUIRED','F06_EXACT_SEPARATE_UNSTARTED_CONSUMER_CLOCK_REQUIRED')
s=s.replace('F06_ORIGINAL_CLOCK_EXPIRED_OR_CHANGED','F06_CONSUMER_CLOCK_EXPIRED_OR_CHANGED')
s=replace(s,"    a=load(c['adapter'],'Root_first_F06_adapter');a.contract_shape(c,bound=False)","    prebirth_reconciled(v)\n    a=load(c['adapter'],'Root_first_F06_adapter');a.contract_shape(c)\n    a.admission(c,json.loads(readref(c['authority']),object_pairs_hook=unique),read=read)")
s=replace(s,"freeze.get('schema')=='frw.F06.ordinary-singleton.source-freeze.v1'","freeze.get('schema')=='frw.F06.existing-R106-first-consumer.source-freeze.v1'")
s=replace(s,"        # One durable claim before issuance: a failure/unknown is reconciliation,\n        # never a request to delete this file, rename the run, issue or send again.\n        new(work/'ROOT-ONCE-INVOCATION.json',encoded({'schema':'frw.Root.F06.one-driver-invocation.v1','at':time.time(),'binding':binding_ref,'run_id':c['run_id'],'source_freeze':v['source_freeze'],'no_retry':True}))", "        # Separate never-started consumer claim. Old once/issuance remain untouched.\n        prebirth_reconciled(v)\n        new(work/'ROOT-FIRST-CONSUMER-ONCE.json',encoded({'schema':'frw.Root.F06.first-consumer-invocation.v1','at':time.time(),'binding':binding_ref,'run_id':c['run_id'],'source_freeze':v['source_freeze'],'existing_authority':c['authority'],'prebirth_closure':v['prebirth_closure'],'old_driver_resume':False,'issuer_invoked':False,'no_retry':True}))")
start=s.index('        for path in AUTHORITY_DIR.glob(');end=s.index("        bound=work/'bot_tester",start)
s=s[:start]+"        # Existing issuance only: no issuer module, scan, entry point or reissue.\n        a.admission(c,json.loads(readref(c['authority']),object_pairs_hook=unique),read=read)\n"+s[end:]
s=replace(s,"'state':'ONE_ORIGINAL_FULL_CONSUMER_NO_RETRY'","'state':'ONE_PREVIOUSLY_UNSTARTED_FULL_CONSUMER_EXISTING_R106_NO_RETRY'")
s=replace(s,"                need(not stops,'F06_STOP_BEFORE_CONSUMER_BIRTH')", "                need(not stops,'F06_STOP_BEFORE_CONSUMER_BIRTH')\n                prebirth_reconciled(v)\n                a.admission(c,json.loads(readref(c['authority']),object_pairs_hook=unique),read=read)\n                need(clock_remaining(clock)>=r['operation_seconds']+r['reserve_seconds'],'F06_CONSUMER_CLOCK_INSUFFICIENT_AT_BIRTH')")
s=replace(s,"'authority':authority,'independent_review':v['independent_review']","'authority':c['authority'],'independent_review':v['independent_review']")
save('root_bind_existing_consumer_once.py',s.encode())
# Inert templates; no actual scenario/authority/clock contents are read or generated.
ns={};exec(compile((W/'f06_source.py').read_bytes(),str(W/'f06_source.py'),'exec'),ns)
def enc(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
save('CONTRACT.UNBOUND.json',enc(ns['unbound']()))
ns={};exec(compile((W/'current207.py').read_bytes(),str(W/'current207.py'),'exec'),dict(ns,__file__=str(W/'current207.py')))
for name in ('SCENARIO.UNBOUND.json','ROOT-REVIEW-TEMPLATES.UNBOUND.json','CURRENT207-PROOF.UNBOUND.json'):
 save(name,(U/name).read_bytes())
inputs={'schema':'frw.Root.F06.existing-R106-first-consumer.v1','status':'UNBOUND_NO_EFFECT','contract':json.loads((W/'CONTRACT.UNBOUND.json').read_bytes()),'source_freeze':None,'independent_review':None,'workdir':None,'slot_identity':None,'expected_binding_sha256':None,'prebirth_closure':{'path':str(O),'bytes':len(raw),'sha256':O_SHA},'prebirth_reconciliation':None}
save('ROOT-CONSUMER-INPUTS.UNBOUND.json',enc(inputs))
closure=json.loads(raw)
r={'schema':'frw.Root.F06.issuer-only-prebirth-reconciliation.v1','operator':'Root','status':'UNBOUND_NOT_GRANTED','created_at':None,'expires_at':None,'prebirth_closure':inputs['prebirth_closure'],'original_run_id':None,'scenario_sha256':None,'existing_authority':None,'old_once':closure['once_claim_preserved'],'old_clock':closure['original_clock']}
for key in ('first_consumer_stage_never_started','old_driver_closed_and_absent','old_once_and_clock_preserved','no_prior_bind_dispatch_canonicalrun_or_unknown','existing_issuance_scope_run_hash_chain_accepted','separate_missing_segment_authorized','no_old_driver_or_issuer_retry'):r[key]=None
save('ROOT-PREBIRTH-RECONCILIATION.UNBOUND.json',enc(r))
save('ROOT-CONSUMER-CLOCK.UNBOUND.json',enc({'schema':'frw.Root.F06.unstarted-consumer-finite-clock.v1','started_at':None,'deadline_at':None,'started_monotonic':None,'deadline_monotonic':None,'boot_id':None}))
print('SOURCE_ONLY_CANDIDATE_WRITTEN')
