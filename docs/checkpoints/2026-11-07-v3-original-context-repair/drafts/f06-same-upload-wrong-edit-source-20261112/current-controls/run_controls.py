"""Explicit synthetic isolated source controls. No real product observation."""
import ast,contextlib,copy,datetime as dt,hashlib,json,math,os,re,resource,sqlite3,stat,subprocess,sys,time,types
from pathlib import Path
B=Path('/home/jericho/.cache/FRW-SOL-V3-F06-SAME-UPLOAD-WRONG-EDIT-SOURCE-20261112')
O=B/'current-controls'; FIX=O/'synthetic-fixture'; FIX.mkdir(mode=0o700,exist_ok=True)
START=time.monotonic(); CPU=time.process_time(); results=[]
raw=(B/'candidate/current_root.py').read_bytes(); before=(B/'before/current_root.py').read_bytes()
m=types.ModuleType('_synthetic_current_root');m.__file__=str(B/'candidate/current_root.py')
# Standard imports are loaded first; from here every open must stay inside B.
def audit(event,args):
    if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
        p=Path(os.fsdecode(args[0]))
        if not p.is_absolute():p=Path.cwd()/p
        if not p.is_relative_to(B):raise AssertionError('CONTROL_FORBIDS_EXTERNAL_FILE_IO')
    if event in ('socket.__new__','socket.connect','subprocess.Popen','os.system'):
        raise AssertionError('CONTROL_FORBIDS_EXTERNAL_EFFECT')
sys.addaudithook(audit)
exec(compile(raw,m.__file__,'exec'),m.__dict__)
def positive(name,f):
    f();results.append({'name':name,'result':'PASS'})
def negative(name,f,match=None):
    try:f()
    except (ValueError,TypeError,KeyError,FileNotFoundError,AssertionError) as e:
        if match is not None:assert match in str(e),(name,type(e).__name__,str(e))
        results.append({'name':name,'result':'REFUSED_AS_REQUIRED','code':str(e)});return
    raise AssertionError(name+' unexpectedly accepted')
def dump(p,v):
    p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    p.write_bytes(m.encoded(v));p.chmod(0o600);return m.ref(p,private=True)
def same(a,b):assertion(a==b)
def assertion(v):
    if not v:raise AssertionError('CONTROL_ASSERTION')
def functions(b):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(b).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
oldfun,newfun=functions(before),functions(raw)
changed={'validate_effect','history','observe','semantic','private_material','final_native'}
unchanged=sorted(set(oldfun)-changed)
positive('inert_import_and_unbound_new_schema',lambda: same(m.unbound_proof()['schema'],'frw.Root.F06.same-upload-wrongedit-preintent.v1'))
positive('unchanged_guards_exact_AST',lambda: assertion(all(oldfun[k]==newfun[k] for k in unchanged)))
negative('unbound_proof_still_refused',lambda:m.validate_proof(m.unbound_proof()),'F06 genuine Root proof unbound')
# One first upload, accepted distinct correct read, historical UNKNOWN and own pristine row.
m.STATE=FIX/'tester-state';runs=m.STATE/'runs';runs.mkdir(mode=0o700,parents=True,exist_ok=True)
s={'steps':[{'request':'SYNTHETIC_WRONG_EDIT_REQUEST_ONLY'}]}
c={'run_id':'synthetic-wrongedit-new','phase':'DOCX-WRONG-EDIT-SAME-UPLOAD','source':{'path':str(FIX/'ciphertext-never-created'),'bytes':1,'sha256':'a'*64},'scenario_sha256':m.digest(m.encoded(s))}
first_run={'id':'synthetic-first','scenario':{'steps':[{'input':{'sha256':'a'*64,'kind':'document'}}]},'status':'STOPPED','phase':'DOCX-WRONG-READ-INGRESS'}
correct_run={'id':'synthetic-correct','scenario':{'steps':[{'request':'SYNTHETIC_PRIOR_CORRECT_READ_REQUEST'}]},'status':'EVIDENCE_READY','phase':'DOCX-CORRECT-READ-SAME-UPLOAD'}
historical={'id':'synthetic-historical','scenario':{'steps':[{'input':{'sha256':'b'*64,'kind':'document'}}]},'status':'STOPPED','send_state':'UNKNOWN'}
first={'canonical_run':dump(runs/'synthetic-first.json',first_run)}
correct={'canonical_run':dump(runs/'synthetic-correct.json',correct_run)}
c['source_reference']={'run_id':first_run['id'],'run_sha256':first['canonical_run']['sha256'],'input_sha256':c['source']['sha256']}
dump(runs/'synthetic-historical.json',historical)
now=time.time();own={'id':c['run_id'],'scenario':s,'scenario_sha256':c['scenario_sha256'],'created_at':dt.datetime.fromtimestamp(now-1,dt.timezone.utc).isoformat(),'deadline':now+299,'step':0,'status':'PREPARED','send_state':'none','sent_ids':[],'seen':[],'message_ids':[],'observations':[],'update_count':0,'last_text':None,'repeat_count':0,'send_attempts':0,'capture_start_offset':0}
dump(runs/(c['run_id']+'.json'),own)
def history():return m.history(c,s,first,correct)
positive('exact_two_dependencies_and_historical_UNKNOWN_preserved',lambda:same(history()['run_ids'],['synthetic-correct','synthetic-first','synthetic-historical']))
for label,key in [('first','synthetic-first'),('correct','synthetic-correct')]:
    p=runs/(key+'.json');saved=p.read_bytes();p.unlink()
    negative('missing_'+label+'_canonical',history,'missing from canonical history')
    p.write_bytes(saved);p.chmod(0o600)
    p.write_bytes(saved+b' ')
    negative('changed_'+label+'_canonical_encoding',history,'identity/encoding drift')
    p.write_bytes(saved)
    row=json.loads(saved);row['synthetic-drift']=True;dump(p,row)
    negative('changed_'+label+'_canonical_hash',history,'changed in canonical history')
    p.write_bytes(saved)
for name,newref in [('same_first',first['canonical_run']),('same_new',m.ref(runs/(c['run_id']+'.json'),private=True)),('outside_runs',{'path':str(FIX/'other.json'),'bytes':12,'sha256':'c'*64})]:
    saved=correct['canonical_run'];correct['canonical_run']=newref
    negative('correct_dependency_'+name,history,'distinct original first')
    correct['canonical_run']=saved
for label,extra in [('same_ciphertext_upload',{'steps':[{'input':{'sha256':'a'*64}}]}),('same_wrongedit_request',s),('same_phase',{'steps':[]})]:
    row={'id':'synthetic-conflict','scenario':extra}
    if label=='same_phase':row['phase']=c['phase']
    p=runs/'synthetic-conflict.json';dump(p,row)
    negative('other_'+label,history)
    p.unlink()
p=runs/(c['run_id']+'.json');saved=p.read_bytes();row=json.loads(saved);row['send_attempts']=1;dump(p,row)
negative('own_nonpristine_run',history,'own row not exact pristine');p.write_bytes(saved)
# Exact current helper calls a pinned local synthetic validator and fails closed.
helper=FIX/'synthetic_validator.py'
correct_doc={'schema':'frw.Root.F06.closed-correct-read.v1','status':'ROOT_BOUND_CORRECT_READ_ACCEPTED','source':c['source'],'source_reference':c['source_reference'],'canonical_run':correct['canonical_run']}
for label,change in [('accepted',None),('ungraded',('status','UNBOUND_NOT_GRANTED')),('wrong_source',('source',{})),('wrong_first',('source_reference',{})),('wrong_schema',('schema','frw.Root.F06.closed-first-upload.v1'))]:
    value=copy.deepcopy(correct_doc)
    if change:value[change[0]]=change[1]
    helper.write_text('def correct_read(c,read,first):\n    return '+repr(value)+'\n');helper.chmod(0o600);c['first_validator']=m.ref(helper,private=True)
    if change:negative('correct_dependency_'+label,lambda:m.correct_dependency(c,first),'semantically accepted correct-read')
    else:positive('correct_dependency_pinned_synthetic_helper',lambda:same(m.correct_dependency(c,first),correct_doc))
helper.write_text(helper.read_text()+'# changed\n')
negative('correct_validator_hash_drift',lambda:m.correct_dependency(c,first),'pinned reference drift')
# Actual semantic() on explicit synthetic pinned judgments; no mocked reference IO.
c.update(first_ingress={'path':str(FIX/'first-manifest.json'),'bytes':1,'sha256':'d'*64},correct_read={'path':str(FIX/'correct-manifest.json'),'bytes':1,'sha256':'e'*64},change_spec={'path':str(FIX/'change.json'),'bytes':1,'sha256':'f'*64},product={'synthetic':1},installation={'product':{'synthetic':1},'runtime_hashes':{'synthetic.py':'0'*64}},root_proofs={})
actual={'history':{'manifest_sha256':'1'*64,'run_ids':['synthetic-correct','synthetic-first','synthetic-historical']},'f06_mutable_boundary':{'native_boundary_sha256':'2'*64,'once_sha256':'3'*64,'ingress_lineage_sha256':'4'*64},'runtime_hashes':c['installation']['runtime_hashes']}
basis=dump(FIX/'synthetic-basis.json',{'synthetic':True})
review={'schema':'frw.Root.F06.history-semantic-once.v1','operator':'Root','status':'ROOT_BOUND','phase':c['phase'],'source':c['source'],'source_reference':c['source_reference'],'first_ingress':c['first_ingress'],'first_upload_closed_and_reconciled':True,'correct_read':c['correct_read'],'change_spec':c['change_spec'],'actual_correct_read_closed_semantically_accepted':True,'latest_supplied_wrong_password_only_authorized':True,'unknown_assumed_absent':False,'history_manifest_sha256':actual['history']['manifest_sha256'],'classified_run_ids':actual['history']['run_ids'],'native_boundary_sha256':'2'*64,'once_sha256':'3'*64,'ingress_lineage_sha256':'4'*64,'equivalent_original_phase_effects':[],'all_profile_history_and_compacted_unlogged_equivalents_reconciled':True,'old_effects_UNKNOWN_and_clocks_preserved':True,'M14_partial_UNKNOWN_preserved_no_replay_or_regrade':True,'all_profile_projection_limit':m.LIMIT,'retained_basis':[basis,basis]}
privacy={'schema':'frw.Root.F06.same-upload-wrongedit-installed-runtime-privacy-review.v1','operator':'Root','status':'ROOT_BOUND','phase':c['phase'],'source_reference':c['source_reference'],'correct_read':c['correct_read'],'change_spec':c['change_spec'],'latest_supplied_wrong_password_only':True,'previous_correct_password_or_history_must_not_be_used':True,'installed_product':c['product'],'runtime_hashes':c['installation']['runtime_hashes'],'genuine_installed_runtime_consumer_observed':True,'no_marker_or_import_bypass':True,'raw_user_chat_retention_separately_reviewed':True,'no_blanket_no_secret_persistence_claim':True,'Standard3_2_data_integrity_verified':False,'runtime_evidence':[basis]}
proof={}
def bind_judgments():
    c['root_proofs']['all_profile_history_semantic_once']=dump(FIX/'synthetic-history-review.json',review)
    c['root_proofs']['private_password_handling']=dump(FIX/'synthetic-runtime-privacy.json',privacy)
    proof.update(history_semantic_review=c['root_proofs']['all_profile_history_semantic_once'],runtime_privacy_review=c['root_proofs']['private_password_handling'])
bind_judgments()
positive('exact_wrongedit_semantic_and_privacy_judgments_synthetic',lambda:m.semantic(proof,c,actual))
for target,fields in [(review,['correct_read','change_spec','actual_correct_read_closed_semantically_accepted','latest_supplied_wrong_password_only_authorized','unknown_assumed_absent','old_effects_UNKNOWN_and_clocks_preserved']), (privacy,['correct_read','change_spec','phase','source_reference','latest_supplied_wrong_password_only','previous_correct_password_or_history_must_not_be_used','Standard3_2_data_integrity_verified'])]:
    for key in fields:
        saved=target[key];target[key]=not saved if type(saved) is bool else None;bind_judgments()
        negative('semantic_review_guard_'+('history_' if target is review else 'privacy_')+key,lambda:m.semantic(proof,c,actual))
        target[key]=saved
bind_judgments()
# Existing private/source-root overlap protection remains actual pure logic.
negative('private_material_in_product_root',lambda:m.disjoint([str(m.H/'private')],[str(m.H)]),'intersects effective product root')
positive('private_material_outside_product_root',lambda:m.disjoint([str(FIX)],[str(m.H)]))
# Actual private_material() logic over isolated synthetic reference metadata.
# Source/dependency collection is stubbed explicitly; no runtime observation.
saved_source,saved_correct,saved_process=m.source,m.correct_dependency,m.read_process
first['private_custody']=dump(FIX/'synthetic-first-custody.json',{'synthetic':True})
nested=O/'private-correct-dependency';nested.mkdir(mode=0o700,exist_ok=True)
change_dir=O/'private-change-spec';change_dir.mkdir(mode=0o700,exist_ok=True)
extra_ref=dump(nested/'synthetic-correct-assessment.json',{'synthetic':True})
c['change_spec']=dump(change_dir/'synthetic-change.json',{'synthetic':True})
c['scenario_ref']=dump(FIX/'synthetic-scenario.json',s)
c['resources']={'clock':basis,'owned_parent_wait_cleanup':basis}
c['installation'].update(closure=basis,source_acceptance=basis)
c['root_proofs']['actual_native_qualification']=basis
c['adapter']=basis
private_correct=dict(correct_doc,assessment=extra_ref)
m.source=lambda effect:types.SimpleNamespace(validate_first=lambda c,read:first)
m.correct_dependency=lambda c,first:private_correct
m.read_process=lambda pid,name:b'SYNTHETIC_PROCESS_NO_PRIVATE_DIRECTORY'
actual.update(source_identity={'synthetic_identity':1},gateway={'pid':123},profile_configs={'synthetic':dump(FIX/'synthetic-config.json',{'synthetic':True})})
lineage={'schema':'frw.Root.F06.retained-g6-source-lineage.v1','operator':'Root','status':'ROOT_BOUND','phase':c['phase'],'source':c['source'],'source_identity':actual['source_identity'],'current_ingress_lineage_sha256':actual['f06_mutable_boundary']['ingress_lineage_sha256'],'original_producer_g6_retained':True,'no_new_producer_or_native_repeat':True,'first_upload_closed_and_reconciled':True,'source_reference':c['source_reference'],'first_ingress':c['first_ingress'],'correct_read':c['correct_read'],'change_spec':c['change_spec'],'actual_correct_read_closed_semantically_accepted':True,'native_qualification':basis,'retained_producer_oracle_basis':[basis]}
privacy.update(effective_product_roots=[str(m.H)],private_roots=sorted([str(B/'candidate'),str(FIX),str(nested),str(change_dir)]),effective_roots_profile_config_refs=actual['profile_configs'],effective_roots_source_basis=[basis])
def bind_private():
    c['root_proofs']['source_ingress_lineage']=dump(FIX/'synthetic-lineage.json',lineage)
    c['root_proofs']['private_password_handling']=dump(FIX/'synthetic-runtime-privacy.json',privacy)
    proof['runtime_privacy_review']=c['root_proofs']['private_password_handling']
proof['contract_effect']={}
def material():return m.private_material(proof,c,actual,FIX/'synthetic-proof.json')
bind_private()
positive('all_new_private_material_directories_covered_synthetic',material)
for label,directory in [('correct_read_nested',nested),('exact_change_spec',change_dir)]:
    saved=privacy['private_roots'];privacy['private_roots']=[p for p in saved if p!=str(directory)];bind_private()
    negative('uncovered_'+label+'_private_directory',material,'all exact private material directories')
    privacy['private_roots']=saved
for key in ('correct_read','change_spec','actual_correct_read_closed_semantically_accepted'):
    saved=lineage[key];lineage[key]=False if type(saved) is bool else None;bind_private()
    negative('lineage_guard_'+key,material,'ingress lineage judgement absent')
    lineage[key]=saved
bind_private();m.source,m.correct_dependency,m.read_process=saved_source,saved_correct,saved_process
# New change_binding must run between shape and exact scenario digest validation.
node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='validate_effect')
calls=[(n.value.func.value.id,n.value.func.attr) for n in node.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name)]
positive('current_validates_exact_change_before_scenario_and_references',lambda:assertion(calls.index(('a','scenario_shape'))<calls.index(('a','change_binding'))))
# Record pins/precise scope. These are source controls only, not product claims.
result={'schema':'frw.Sol.wrongedit.current-source-controls.v1','assignment':'SOL-T30-WRONGEDIT-CURRENT#1','status':'SOURCE_CONTROLS_PASS','candidate_current_sha256':hashlib.sha256(raw).hexdigest(),'before_current_sha256':hashlib.sha256(before).hexdigest(),'controls':results,'unchanged_guard_function_AST':unchanged,'synthetic_fixtures':True,'runtime_observation':'NOT_RUN','actual_correct_read':'UNBOUND_NOT_ESTABLISHED','actual_wrong_edit':'NOT_RUN','synthetic_collection_stubs':['source.validate_first in private_material controls only','correct_dependency in private_material controls only','read_process in private_material controls only'],'prior_control_harness_failures':[{'artifact':'controls-attempt1.log','cause':'stdlib sqlite3 not preimported before own B-only IO audit; fixed preimports'},{'artifact':'controls-attempt2.log','cause':'ast.unparse lazy stdlib import denied by own B-only IO audit; replaced with direct AST attribute access'}],'permissions':{'effect':'source-only own B','files':'0600','directories':'0700'},'limits':{'wall_seconds':90,'cpu_seconds':60,'max_rss_bytes':512*1024**2,'cpus':2,'disk_bytes':64*1024**2},'elapsed_wall_seconds':round(time.monotonic()-START,6),'elapsed_cpu_seconds':round(time.process_time()-CPU,6),'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(O/'RESULT.json').write_bytes(m.encoded(result));(O/'RESULT.json').chmod(0o600)
print(json.dumps({'status':result['status'],'controls':len(results),'candidate_current_sha256':result['candidate_current_sha256'],'wall_seconds':result['elapsed_wall_seconds'],'cpu_seconds':result['elapsed_cpu_seconds']}))
