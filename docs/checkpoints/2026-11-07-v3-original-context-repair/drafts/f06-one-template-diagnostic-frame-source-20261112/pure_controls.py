"""Own synthetic controls; never executes a frame/main or loads UNO/Office."""
import ast,copy,hashlib,json,os,pathlib,stat,sys,types,tempfile,shutil
B=pathlib.Path(__file__).parent;C=B/'candidate';sys.dont_write_bytecode=True
# The contract's imports/constants/functions are inert; execute no main/frame.
ns={'__file__':str(C/'f06_contract.py'),'__name__':'f06_contract'}
exec(compile(ast.parse((C/'f06_contract.py').read_text()),str(C/'f06_contract.py'),'exec'),ns)
c=types.ModuleType('f06_contract');c.__dict__.update(ns);sys.modules['f06_contract']=c

def extract(file,names,extra):
 tree=ast.parse((C/file).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(nodes)==len(names)
 d=dict(extra);exec(compile(ast.Module(nodes,type_ignores=[]),file,'exec'),d);return d
rows=[]
def check(name,fn):
 try:fn();rows.append({'name':name,'pass':True})
 except BaseException as e:rows.append({'name':name,'pass':False,'error_class':type(e).__name__})
def refused(fn):
 try:fn()
 except (ValueError,KeyError,TypeError):return
 raise AssertionError('EXPECTED_REFUSAL')
def pin(path,sha='a'*64,size=10):return dict(path=path,bytes=size,sha256=sha,identity=[1,2,stat.S_IFREG|0o600,os.getuid(),os.getgid(),1,size,3,4])
credential=pin('/synthetic/credential.private.json')
source=pin('/synthetic/retained-source.ott',c.SELECTED_SHA)
row={**source,'fixture_id':c.SELECTED_ID,'format':'ott','role':'source','fixture_profile':c.PROFILES[0],'semantic':'BEFORE','mime':'application/vnd.oasis.opendocument.text-template','service':'com.sun.star.text.TextDocument','filter':'writer8_template','staged_name':'retained-source.ott','native_source_ciphertext':dict(source)}
manifest=dict(schema='friday.f06.one-template-selected.v1',state='ROOT_BOUND_RETAINED_METADATA_NOT_EXECUTION_AUTHORITY',assignment=c.ASSIGNMENT,selected_count=1,selected_fixture_ids=[c.SELECTED_ID],expected_Office_stores=0,expected_Office_password_probes=1,whole_F06_accepted=False,as_template=False,credential=credential,fixtures=[row])
check('exact_narrow_manifest',lambda:c.manifest_contract(manifest))
for name,mut in [('wrong_input_hash',lambda m:m['fixtures'][0].update(sha256='b'*64)),('wrong_template',lambda m:m['fixtures'][0].update(format='ots')),('extra_rows',lambda m:m['fixtures'].append(copy.deepcopy(m['fixtures'][0]))),('probe_expansion',lambda m:m.update(expected_Office_password_probes=18)),('store_nonzero',lambda m:m.update(expected_Office_stores=1)),('bool_count',lambda m:m.update(selected_count=True)),('alias_secret',lambda m:m['credential'].update(path=m['fixtures'][0]['path'])),('extra_metadata',lambda m:m.update(payload='FORBIDDEN')),('credential_digest_unbound',lambda m:m['credential'].update(sha256=None)),('source_identity_drift',lambda m:m['fixtures'][0]['identity'].__setitem__(6,12)),('source_relation_drift',lambda m:m['fixtures'][0]['native_source_ciphertext'].update(sha256='f'*64))]:
 def run(mut=mut):m=copy.deepcopy(manifest);mut(m);refused(lambda:c.manifest_contract(m))
 check(name,run)
entry=extract('root_entry.py',{'require','assemble'},{})
binding=json.loads((C/'ROOT-BINDINGS.TEMPLATE.json').read_bytes());binding.update(state='ROOT_BOUND_NO_EFFECT_YET',operation_key='one-template-diag-synthetic',uid=123,boot_id='syntheticboot',source_pins_sha256='d'*64,limits=c.LIMITS,original_operation_start_monotonic=10,nonce='1'*32)
for k in ('source_review','runtime_authority','fresh_boundary','original18_closure','output_manifest','credential_source'):binding[k]=copy.deepcopy(credential)
check('inert_unbound_template_refused',lambda:refused(lambda:entry['assemble'](json.loads((C/'ROOT-BINDINGS.TEMPLATE.json').read_bytes()),'d'*64,uid=123,boot='syntheticboot',now='fixed',monotonic_now=11)))
check('pure_assembly_no_authority_fabrication',lambda:entry['assemble'](binding,'d'*64,uid=123,boot='syntheticboot',now='fixed',monotonic_now=11))
for name,mut in [('stale_original_clock',lambda b:b.update(original_operation_start_monotonic=-200)),('different_boot',lambda b:b.update(boot_id='old')),('source_hash_drift',lambda b:b.update(source_pins_sha256='b'*64)),('runtime_authority_none',lambda b:b.update(runtime_authority=None)),('extra_binding_field',lambda b:b.update(unknown=True)),('limits_expansion',lambda b:b.update(limits={**c.LIMITS,'max_password_probes':18}))]:
 def run(mut=mut):b=copy.deepcopy(binding);mut(b);refused(lambda:entry['assemble'](b,'d'*64,uid=123,boot='syntheticboot',now='fixed',monotonic_now=11))
 check(name,run)
# Authenticate runtime proof graph at its actual consumer using synthetic
# fullpins/read function only; never read a real protected input.
def proof_case(change=None):
 a=dict(source_pins_sha256='e'*64,operation_key='one-template-diag-synthetic',boot_id='syntheticboot',nonce='1'*32,original_operation_start_monotonic=10)
 for k in ('original18_closure','source_review','runtime_authority','fresh_boundary'):a[k]=pin('/synthetic/'+k+'.json')
 a['original18_closure']=pin(str(c.ORIGINAL18_PATH),c.ORIGINAL18_SHA)
 a['output_manifest']=pin('/synthetic/selected.json')
 review=dict(state='ROOT_ACCEPTED_ONE_TEMPLATE_DIAGNOSTIC_SOURCE',execution_authority=False,source_pins_sha256=a['source_pins_sha256'],task24_freeze_sha256=c.TASK24_FREEZE_SHA,findings_remaining=[])
 authority=dict(state='ROOT_GRANTED_ONE_MISSING_CONVERSION_OBSERVATION',operation_key=a['operation_key'],source_pins_sha256=a['source_pins_sha256'],selected_manifest=a['output_manifest'],source_review=a['source_review'],original18_closure=a['original18_closure'],fresh_boundary=a['fresh_boundary'],original18_replayed=False,original_strict_all_pass=False,whole_F06_accepted=False,max_document_loads=1,max_getRequest_calls=1,stores=0,correct_password_only=True,limits=c.limits(c.MODE),boot_id=a['boot_id'],nonce=a['nonce'],original_operation_start_monotonic=10)
 objects={a['original18_closure']['path']:{},a['source_review']['path']:review,a['runtime_authority']['path']:authority}
 if change:change(a,review,authority)
 g=c.diagnostic_acceptance.__globals__;old=g['runtime_pin_check'];g['runtime_pin_check']=lambda r:(objects[r['path']],r)
 try:c.diagnostic_acceptance(a)
 finally:g['runtime_pin_check']=old
check('actual_proof_consumer_exact_graph',lambda:proof_case())
for name,mut in [('authority_not_source_acceptance',lambda a,r,u:u.update(state=r['state'])),('authority_nonce_drift',lambda a,r,u:u.update(nonce='0'*32)),('authority_fresh_pin_drift',lambda a,r,u:u.update(fresh_boundary=pin('/synthetic/oldfresh.json'))),('authority_wrong_source',lambda a,r,u:u.update(source_pins_sha256='a'*64)),('old18_cannot_promote',lambda a,r,u:u.update(original_strict_all_pass=True)),('authority_bool_one_refused',lambda a,r,u:u.update(max_getRequest_calls=True)),('authority_store_refused',lambda a,r,u:u.update(stores=1)),('source_findings_open',lambda a,r,u:r.update(findings_remaining=['OPEN']))]:
 check(name,lambda mut=mut:refused(lambda:proof_case(mut)))

# Actual local dummy copies exercise current tracked-stage and failure audit.
# No original retained ciphertext or real secret is read. Do not serialize dummies.
tmp=pathlib.Path(tempfile.mkdtemp(prefix='synthetic-',dir=B));os.chmod(tmp,0o700)
try:
 def local(name,data):p=tmp/name;p.write_bytes(data);p.chmod(0o600);return c.stable(p)[1]
 mp=local('manifest.json',b'{}');cp=local('credential.json',b'{"password":"synthetic"}');sp=local('dummy.ott',b'NOT_A_DOCUMENT_SYNTHETIC_CIPHERTEXT')
 fake_manifest={'selected_count':1,'selected_fixture_ids':[c.SELECTED_ID],'fixtures':[{'fixture_id':c.SELECTED_ID,'staged_name':c.NAMES[0]}]}
 fake_rows=[{**sp,'fixture_id':c.SELECTED_ID,'native_source_ciphertext':dict(sp)}]
 fake=types.SimpleNamespace(**{n:getattr(c,n)for n in ('need','MODE','identity','stable','private','save')})
 fake.output_inputs=lambda a:(fake_manifest,mp,fake_rows,cp)
 fake.diagnostic_acceptance=lambda a:None
 fake.credential_metadata=lambda ref:(ref,c.identity(pathlib.Path(ref['path']).lstat()))
 funcs=extract('run_once.py',{'matches','copy_private','stage','readonly_after'},{'c':fake,'os':os,'Path':pathlib.Path})
 def stage_case(fail):
  op=tmp/('partial'if fail else'complete');op.mkdir(mode=0o700);custody={};ad={'selected_count':1,'selected_fixture_ids':[c.SELECTED_ID],'credential_source_identity':cp['identity'],'credential_source':cp}
  original=funcs['copy_private']
  calls=[]
  def broken(source,target,expected):
   calls.append(str(target))
   if len(calls)==2:
    target.write_bytes(b'PARTIAL');target.chmod(0o600);raise OSError('SYNTHETIC')
   return original(source,target,expected)
  if fail:funcs['copy_private']=broken
  try:
   try:funcs['stage'](c.MODE,op,ad,custody)
   except OSError:assert fail
   report={'namespace_closed':True,'state':'FAILED_OR_PARTIAL_PRESERVED_NO_REPLAY'};funcs['readonly_after'](ad,custody,report)
   assert len(report['original_inputs_after_observations'])==4
   assert all(x['cas_verified']for x in report['original_inputs_after_observations'])
   assert report['readonly_custody_after_cas'] is (not fail)
   if fail:
    assert len(custody['copy_attempts'])==2 and custody['copy_attempts'][1]['copy_completed']is False
    assert report['staged_copies_after_observations'][1]['cas_verified']is False
    assert (op/'inputs/native-outputs/retained-source.ott').read_bytes()==b'PARTIAL'
  finally:funcs['copy_private']=original
 check('complete_stage_and_after_full_cas',lambda:stage_case(False))
 check('partial_copy_preserved_independent_all_original_after_checks',lambda:stage_case(True))
finally:shutil.rmtree(tmp)
# Raw CLI lexical guard: argparse must not normalize aliases before canonical.
for name,arg in [('root_entry.py','bindings'),('root_frame.py','admission'),('run_once.py','admission')]:
 def lexical(name=name,arg=arg):
  tree=ast.parse((C/name).read_text())
  calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='add_argument' and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value=='--'+arg]
  assert len(calls)==1 and not any(k.arg=='type' and isinstance(k.value,ast.Name) and k.value.id=='Path' for k in calls[0].keywords)
 check('raw_CLI_spelling_preserved_'+name,lexical)

# Rootconsumer runtime domain uses actual guards; old manager/ownership code is
# reused source-only, not invoked here. Verify no accidental runtime at import.
for file in C.glob('*.py'):
 check('grammar312_'+file.name,lambda file=file:ast.parse(file.read_text(),filename=str(file),feature_version=(3,12)))
print(json.dumps({'schema':'task25.pure-controls.v1','synthetic_only':True,'Office_or_UNO_execution':False,'real_inputs_or_credentials_read':False,'observed_limits':{'CPU':__import__('resource').getrlimit(__import__('resource').RLIMIT_CPU),'AS':__import__('resource').getrlimit(__import__('resource').RLIMIT_AS),'affinity':sorted(os.sched_getaffinity(0))},'controls':rows,'all_pass':all(r['pass']for r in rows)},sort_keys=True))
raise SystemExit(0 if all(r['pass']for r in rows)else 1)
