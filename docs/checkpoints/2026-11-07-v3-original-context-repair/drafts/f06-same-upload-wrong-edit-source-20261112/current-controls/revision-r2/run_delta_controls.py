"""R2-only synthetic metadata privacy controls; no old46 rerun or real secrets."""
import ast,contextlib,copy,datetime as dt,hashlib,json,math,os,re,resource,sqlite3,stat,subprocess,sys,time,types
from pathlib import Path
B=Path('/home/jericho/.cache/FRW-SOL-V3-F06-SAME-UPLOAD-WRONG-EDIT-SOURCE-20261112');O=B/'current-controls/revision-r2';F=O/'fixtures';F.mkdir(mode=0o700,exist_ok=True)
START=time.monotonic();CPU=time.process_time();checks=[];blocked_reads=[]
p=B/'candidate/current_root.py';raw=p.read_bytes();r1=(O/'current_root.r1.py').read_bytes()
m=types.ModuleType('_R2_synthetic_current');m.__file__=str(p)
def audit(event,args):
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  path=Path(os.fsdecode(args[0]));path=path if path.is_absolute() else Path.cwd()/path
  if not path.is_relative_to(B) or path in blocked_reads:raise AssertionError('R2_UNAUTHORIZED_FILE_OPEN')
 if event in ('socket.__new__','socket.connect','subprocess.Popen','os.system'):raise AssertionError('R2_EXTERNAL_EFFECT_FORBIDDEN')
sys.addaudithook(audit);exec(compile(raw,str(p),'exec'),m.__dict__)
def check(name,fn):fn();checks.append({'name':name,'result':'PASS'})
def refuse(name,fn,code):
 try:fn()
 except (ValueError,KeyError,AssertionError) as e:
  assert code in str(e),(name,str(e));checks.append({'name':name,'result':'REFUSED_AS_REQUIRED','code':str(e)});return
 raise AssertionError(name+' unexpectedly accepted')
def need(v):
 if not v:raise AssertionError('R2_ASSERT')
def write(path,value):
 path.parent.mkdir(mode=0o700,parents=True,exist_ok=True);path.write_bytes(m.encoded(value));path.chmod(0o600);return m.ref(path,private=True)
def fake(path):blocked_reads.append(path);return {'path':str(path),'bytes':9,'sha256':'a'*64}
basis=write(F/'runtime-basis.json',{'synthetic':True});prior=fake(F/'private-preparation/previous-correct-scenario.json');consumer=fake(F/'private-preparation/old-consumer.py');oracle=fake(F/'private-preparation/plaintext-oracle-basis.json');other_oracle=fake(F/'private-preparation/assessment-oracle-basis.json')
# Raw original tester artifacts remain under STATE; we only use their refs here.
raw_refs={k:fake(m.STATE/('synthetic-'+k+'.json')) for k in ('canonical','ack','task','window','terminal')}
binding={'schema':'SYNTHETIC_VALIDATED_CORRECT_BINDING','source':consumer,'contract':{'scenario_ref':prior,'authority':fake(F/'private-preparation/old-authority.json'),'adapter':fake(F/'private-preparation/old-adapter.py'),'footer':fake(F/'private-preparation/old-footer.txt'),'actual_root_B_checker':fake(F/'private-preparation/old-current.py'),'root_current_proof':fake(F/'private-preparation/old-current-proof.json'),'root_proofs':{'prior_private_oracle':oracle},'resources':{'clock':fake(F/'private-preparation/old-clock.json'),'owned_parent_wait_cleanup':fake(F/'private-preparation/old-cleanup.json')}}}
custody={'schema':'SYNTHETIC_VALIDATED_ORIGINAL_CUSTODY','terminal_receive':raw_refs['terminal'],'retained_basis':[oracle],'bound_source':consumer}
assessment={'schema':'SYNTHETIC_VALIDATED_ASSESSMENT','retained_basis':[other_oracle]}
correct={'schema':'SYNTHETIC_VALIDATED_CORRECT_METADATA','canonical_run':raw_refs['canonical'],'ack':raw_refs['ack'],'task':raw_refs['task'],'window':raw_refs['window']}
closure={'schema':'SYNTHETIC_VALIDATED_CLOSURE'}
first={'private_custody':basis}
c={'scenario_ref':basis,'source':dict(basis),'first_ingress':basis,'first_validator':basis,'correct_read':basis,'change_spec':basis,'root_proofs':{'actual_native_qualification':basis},'resources':{'clock':basis,'owned_parent_wait_cleanup':basis},'installation':{'closure':basis,'source_acceptance':basis},'source_reference':{'run_id':'synthetic-first','run_sha256':'b'*64,'input_sha256':basis['sha256']},'phase':'DOCX-WRONG-EDIT-SAME-UPLOAD'}
actual={'profile_configs':{'synthetic':write(F/'config.json',{'synthetic':True})},'gateway':{'pid':123},'source_identity':{'synthetic':True},'f06_mutable_boundary':{'ingress_lineage_sha256':'c'*64}}
lineage={'schema':'frw.Root.F06.retained-g6-source-lineage.v1','operator':'Root','status':'ROOT_BOUND','phase':c['phase'],'source':c['source'],'source_identity':actual['source_identity'],'current_ingress_lineage_sha256':'c'*64,'original_producer_g6_retained':True,'no_new_producer_or_native_repeat':True,'first_upload_closed_and_reconciled':True,'source_reference':c['source_reference'],'first_ingress':basis,'correct_read':basis,'change_spec':basis,'actual_correct_read_closed_semantically_accepted':True,'native_qualification':basis,'retained_producer_oracle_basis':[basis]}
c['root_proofs']['source_ingress_lineage']=write(F/'lineage.json',lineage)
privacy={'effective_product_roots':[str(m.H)],'private_roots':sorted([str(B/'candidate'),str(O),str(m.STATE)]),'effective_roots_profile_config_refs':actual['profile_configs'],'effective_roots_source_basis':[basis]}
proof={'runtime_privacy_review':None,'contract_effect':{}}
m.source=lambda effect:types.SimpleNamespace(validate_first=lambda c,read:first)
m.correct_dependency=lambda c,first:correct
m.read_process=lambda pid,name:b'SYNTHETIC_NO_PRIVATE_DIRECTORY_METADATA'
def bind():
 correct['correct_binding']=write(F/'binding.json',binding)
 closure['original_consumer_custody']=write(F/'custody.json',custody)
 correct['closure']=write(F/'closure.json',closure)
 correct['assessment']=write(F/'assessment.json',assessment)
 proof['runtime_privacy_review']=write(F/'privacy.json',privacy)
 c['root_proofs']['private_password_handling']=proof['runtime_privacy_review']
def material():m.private_material(proof,c,actual,F/'current-proof.json')
bind()
check('covered_previous_scenario_binding_custody_and_oracle_refs_pass_without_opening_them',material)
# Every original tester path was denied by the IO audit but metadata-only admission passes.
check('original_STATE_raw_chat_ACK_task_canonical_exception_remains',lambda:need(str(m.STATE) in privacy['private_roots']))
def product_ref_case(name,container,key):
 saved=container[key];path=m.H/'synthetic-private-preparation'/name
 container[key]=fake(path);saved_roots=privacy['private_roots'];privacy['private_roots']=sorted(saved_roots+[str(path.parent)]);bind()
 refuse(name+'_under_effective_product_root',material,'intersects effective product root')
 container[key]=saved;privacy['private_roots']=saved_roots;bind()
product_ref_case('previous-correct-scenario.json',binding['contract'],'scenario_ref')
product_ref_case('previous-bound-consumer.py',binding,'source')
product_ref_case('previous-root-proof.json',binding['contract']['root_proofs'],'prior_private_oracle')
product_ref_case('old-clock.json',binding['contract']['resources'],'clock')
# Custody/assessment nested oracle refs must participate in private root coverage.
for label,container,key in [('custody_terminal',custody,'terminal_receive'),('custody_bound_source',custody,'bound_source')]:
 product_ref_case(label+'.json',container,key)
for label,container in [('custody_basis',custody),('assessment_basis',assessment)]:
 saved=container['retained_basis'];path=m.H/'synthetic-private-preparation'/(label+'.json');container['retained_basis']=[fake(path)];saved_roots=privacy['private_roots'];privacy['private_roots']=sorted(saved_roots+[str(path.parent)]);bind()
 refuse(label+'_under_product_root',material,'intersects effective product root')
 container['retained_basis']=saved;privacy['private_roots']=saved_roots;bind()
# A separately protected external preparation directory passes; an uncovered one fails.
saved=binding['contract']['scenario_ref'];external=B/'current-controls/r2-external-protected';binding['contract']['scenario_ref']=fake(external/'previous-scenario.json');bind()
refuse('uncovered_previous_scenario_directory',material,'all exact private material directories')
privacy['private_roots']=sorted(privacy['private_roots']+[str(external)]);bind()
check('separate_covered_previous_scenario_directory_passes',material)
binding['contract']['scenario_ref']=saved;privacy['private_roots'].remove(str(external));bind()
for name,path in [('binding',F/'binding.json'),('closure',F/'closure.json'),('custody',F/'custody.json'),('assessment',F/'assessment.json')]:
 original=path.read_bytes();path.write_bytes(original+b' ')
 refuse(name+'_metadata_pin_drift',material,'private metadata pin drift')
 path.write_bytes(original)
# Historical permission identity is retained; metadata allows the same owned0664 as validator.
p=F/'binding.json';p.chmod(0o664);before_stat=p.stat();check('historical_owned0664_metadata_kept_without_chmod',material);need(stat.S_IMODE(p.stat().st_mode)==0o664 and p.stat().st_ino==before_stat.st_ino);p.chmod(0o600)
saved=binding['contract']['scenario_ref'];binding['contract']['scenario_ref']=dict(saved,path=str(F/'private-preparation/../alias.json'));bind()
refuse('nested_ref_lexical_alias',material,'LEXICAL_PATH_ALIAS_REFUSED');binding['contract']['scenario_ref']=saved;bind()
# Bounded four-document collector never follows an arbitrary metadata graph.
saved=dict(binding);chain=[];at=chain
for _ in range(34):new=[];at.append(new);at=new
binding['synthetic_deep']=chain;bind();refuse('bounded_metadata_depth',material,'bounded correct-read private metadata exceeded');binding.clear();binding.update(saved);bind()
binding['synthetic_many_refs']=[prior]*2049;bind();refuse('bounded_metadata_reference_count',material,'bounded correct-read private-material ref required');del binding['synthetic_many_refs'];bind()
binding['synthetic_many_nodes']=[0]*8193;bind();refuse('bounded_metadata_node_count',material,'bounded correct-read private metadata exceeded');del binding['synthetic_many_nodes'];bind()
saved=correct['correct_binding'];correct['correct_binding']=dict(saved,bytes=1024**2+1);refuse('bounded_metadata_bytes_before_open',material,'bounded pinned correct-read metadata required');correct['correct_binding']=saved
check('covered_final_metadata_still_passes',material)
def funcs(b):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(b).body if isinstance(n,ast.FunctionDef)}
f1,f2=funcs(r1),funcs(raw);unchanged=sorted(set(f1)-{'private_material'})
check('only_private_material_function_changed',lambda:need(set(f1)==set(f2) and all(f1[k]==f2[k] for k in unchanged)))
a1=[ast.dump(n,include_attributes=False) for n in ast.parse(r1).body if isinstance(n,ast.Assign)];a2=[ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,ast.Assign)]
check('all_source_origin_runtime_pins_and_constants_unchanged',lambda:need(a1==a2))
result={'schema':'frw.Sol.wrongedit.current-source-controls.revision-r2.v1','assignment':'SOL-T30-WRONGEDIT-CURRENT#1','status':'AFFECTED_SOURCE_DELTA_CONTROLS_PASS','r1_current_sha256':hashlib.sha256(r1).hexdigest(),'r2_current_sha256':hashlib.sha256(raw).hexdigest(),'r1_result_sha256':hashlib.sha256((B/'current-controls/RESULT.json').read_bytes()).hexdigest(),'checks':checks,'unchanged_function_AST_count':len(unchanged),'retained_prior46controls':'NOT_RERUN_UNCHANGED','synthetic_validated_dependency_stubs':True,'forbidden_reference_bodies_not_opened':len(blocked_reads),'metadata_open_scope':['correct_binding','closure','original_consumer_custody','assessment'],'actual_correct_read':'UNBOUND','runtime_wrongedit':'NOT_RUN','limits':{'wall_seconds':90,'cpu_seconds':60,'max_rss_bytes':512*1024**2,'cpus':2},'actuals':{'wall_seconds':round(time.monotonic()-START,6),'cpu_seconds':round(time.process_time()-CPU,6),'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024},'completed_at_moscow':dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).isoformat()}
(O/'RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');(O/'RESULT.json').chmod(0o600)
print(json.dumps({'status':result['status'],'checks':len(checks),'source_sha256':result['r2_current_sha256'],'actuals':result['actuals']}))
