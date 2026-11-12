"""Bounded source/in-memory checks. Never import helper or accepted candidates."""
import ast
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import types

HERE = Path(__file__).resolve().parent
HELPER = HERE / 'prepare-post-args-root-office-caller.py'
FRAME = Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-POST-ARGS-COMPAT-OFFICE-FRAME-SOURCE-20261112')
TEXT = HELPER.read_text()
TREE = ast.parse(TEXT)
CTEXT = (FRAME / 'candidate/f06_contract.py').read_text()
RTEXT = (FRAME / 'candidate/root_frame.py').read_text()
ETEXT = (FRAME / 'candidate/root_entry.py').read_text()
ROWS = []

def check(name, fn):
    try:
        fn()
    except BaseException as exc:
        ROWS.append(dict(name=name, passed=False, exception_class=type(exc).__name__, code=str(exc)))
    else:
        ROWS.append(dict(name=name, passed=True))

def equal(a, b):
    if a != b:
        raise AssertionError((a, b))

def reject(fn, code=None):
    try:
        fn()
    except (ValueError, KeyError) as exc:
        if code is not None:
            equal(str(exc), code)
        return
    raise AssertionError('accepted invalid protocol')

def extract(text, names, env):
    tree = ast.parse(text)
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    equal({n.name for n in nodes}, set(names))
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<synthetic-extracted-functions>', 'exec'), env)

def need(value, code):
    if not value:
        raise ValueError(code)

def instance():
    files, pins, events = {}, {}, []
    class VPath(PurePosixPath):
        def exists(self): return str(self) in files or str(self) in pins
        def resolve(self, strict=False): return self
        def stat(self):
            return types.SimpleNamespace(st_mode=0o100600, st_uid=1000, st_nlink=1, st_size=pins.get(str(self), {}).get('bytes', len(files.get(str(self), b''))))
        def lstat(self): return self.stat()
        def read_text(self):
            return {'/proc/sys/kernel/random/boot_id': 'synthetic-boot', '/proc/meminfo': 'MemAvailable: 4000000 kB', '/proc/pressure/cpu': 'synthetic CPU pressure', '/proc/pressure/io': 'synthetic IO pressure'}[str(self)]
        def iterdir(self):
            equal(str(self), '/proc')
            return iter([])
    c = types.SimpleNamespace()
    def pin(path, size=100, sha=None):
        key = str(path)
        if key not in pins:
            pins[key] = dict(path=key, bytes=size, sha256=sha or hashlib.sha256(key.encode()).hexdigest(), identity=[1, len(pins)+1, 0o100600, 1000, 1000, 1, size, 1, 1])
        return copy.deepcopy(pins[key])
    def put(path, obj, sha=None, size=100):
        files[str(path)] = copy.deepcopy(obj)
        return pin(path, size, sha)
    def read(path):
        events.append(('read', str(path)))
        return copy.deepcopy(files[str(path)])
    clock = types.SimpleNamespace(monotonic=lambda: 1000.0, process_time=lambda: 0.2)
    osmock = types.SimpleNamespace(getuid=lambda:1000, getpid=lambda:4242, sched_getaffinity=lambda _:{0,1,2,3},
        O_RDONLY=0, O_NOFOLLOW=1, O_NONBLOCK=2, open=lambda *args:7, close=lambda _:None,
        fstat=lambda _:types.SimpleNamespace(st_mode=0o100600, st_uid=1000, st_nlink=1, st_size=0), path=types.SimpleNamespace(lexists=lambda p:str(p) in files))
    osmock.execv = lambda exe, argv: events.append(('execv', exe, argv))
    env = dict(Path=VPath, hashlib=hashlib, json=json, stat=stat, time=clock, os=osmock, print=lambda *args,**kwargs:None,
        resource=types.SimpleNamespace(RUSAGE_CHILDREN=0, getrusage=lambda _:types.SimpleNamespace(ru_utime=0.0,ru_stime=0.0)),
        fcntl=types.SimpleNamespace(LOCK_EX=1,LOCK_NB=2,flock=lambda *args:None), uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex='a'*32)))
    assigns = [node for node in TREE.body if isinstance(node, ast.Assign) and all(isinstance(t,ast.Name) for t in node.targets)]
    exec(compile(ast.Module(body=assigns, type_ignores=[]), '<synthetic-constants>', 'exec'), env)
    extract(TEXT, {'require','budget','source','full','history','accepted_review','prepare','execute'}, env)
    env.update(load=read, digest=lambda p:pin(p)['sha256'], now=lambda:'2026-11-12T00:00:00+03:00')
    def save(path, value):
        need(str(path) not in files, 'SYNTHETIC_O_EXCL')
        events.append(('save', str(path)))
        put(path, value)
    env['save'] = save
    cenv = dict(Path=VPath, os=osmock, stat=stat, re=re, json=json, need=need)
    names = {'ASSIGNMENT','MODE','LIMITS','SELECTED_ID','SELECTED_SHA','PROFILES','NAMES','IDENTITY_FIELDS','REF_KEYS','ORIGINAL18_PATH','ORIGINAL18_SHA','TASK24_FREEZE_SHA','TASK25_FREEZE_SHA','TASK27_FREEZE_SHA','PREVIOUS_CLASS1_SUMMARY_SHA','OPERATION_KEY','POSTCHANGE_PURPOSE','PRE_STAGE_CREDENTIAL_PATHS'}
    nodes = [n for n in ast.parse(CTEXT).body if isinstance(n, ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in names]
    equal({n.targets[0].id for n in nodes}, names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<synthetic-contract-constants>','exec'),cenv)
    extract(CTEXT, {'limits','operation','exact_json','reference_shape','full_pin_shape','manifest_contract','diagnostic_acceptance','output_inputs'},cenv)
    cenv.update(B=env['C'])
    cenv['runtime_pin_check'] = lambda ref:(read(ref['path']),pin(ref['path']))
    def credential(ref):
        cenv['full_pin_shape'](ref)
        equal(ref, pin('/synthetic-private/credential', 8))
        return copy.deepcopy(ref),copy.deepcopy(ref['identity'])
    cenv['credential_metadata'] = credential
    def reference_read(ref, forbidden=(), limit=8*1024**2):
        need(ref['path'] not in forbidden, 'SYNTHETIC_CREDENTIAL_BODY_READ_FORBIDDEN')
        equal(ref, pin(ref['path']))
        obj = read(ref['path']) if ref['path'] in files else b'NOT_A_REAL_DOCUMENT'
        return json.dumps(obj).encode() if not isinstance(obj,bytes) else obj,pin(ref['path'])
    cenv['reference_read'] = reference_read
    cenv['decode'] = json.loads
    for key,value in cenv.items():
        if key != '__builtins__':setattr(c,key,value)
    c.SLOT = VPath('/synthetic-slot')
    c.identity = lambda _: [1,2,0o100600,1000,1000,1,0,1,1]
    c.stable = lambda path:(b'SYNTHETIC_METADATA_ONLY', pin(path))
    c.bank_snapshot = lambda:{'synthetic_critical4':'unchanged'}
    c.recipe_check = lambda:(dict(sha256=env['SOURCE_SHA']),[])
    c.within = lambda reserve=0:env['budget'](1000.0)
    c.retention_snapshot = lambda root:equal(root,str(env['T']))
    c.credential_metadata = credential
    c.canonical = lambda path:VPath(path)
    c.output_inputs = cenv['output_inputs']
    review = dict(state='ROOT_ACCEPTED_POST_ARGS_COMPAT_ONE_TEMPLATE_SOURCE', execution_authority=False, source_pins_sha256=env['SOURCE_SHA'], task24_freeze_sha256=c.TASK24_FREEZE_SHA,
        task25_sourcefreeze_sha256=c.TASK25_FREEZE_SHA, task27_sourcefreeze_sha256=c.TASK27_FREEZE_SHA, previous_class1_summary_sha256=c.PREVIOUS_CLASS1_SUMMARY_SHA,
        postchange_purpose=c.POSTCHANGE_PURPOSE, findings_remaining=[], source_freeze=dict(path=str(env['T']/'SOURCE-FREEZE.json'),sha256=env['FREEZE_SHA']))
    put(env['ACCEPT'],review,env['ACCEPT_SHA'])
    put(c.ORIGINAL18_PATH,dict(execution_closed=True,parent_absent_or_different_birth=True,original_and_staged_full_custody_verified=True),c.ORIGINAL18_SHA)
    put(env['PREVIOUS'],dict(state='ONE_DIAGNOSTIC_COMPLETED_NEW_OBSERVED_SETTER_FAILURE_PARTIAL_CLOSED',owned_actor_namespace_unit_and_parent_closed=True,slot_free=True,full_original_staged_bank_source_admission_CAS_after_closure=True),c.PREVIOUS_CLASS1_SUMMARY_SHA)
    row = dict(pin('/synthetic-private/retained-source.ott',4624,c.SELECTED_SHA), fixture_id=c.SELECTED_ID,format='ott',role='source',fixture_profile=c.PROFILES[0],semantic='BEFORE',mime='application/vnd.oasis.opendocument.text-template',service='com.sun.star.text.TextDocument',filter='writer8_template',staged_name=c.NAMES[0])
    row['native_source_ciphertext'] = {k:row[k] for k in env['PIN_KEYS']}
    cred = pin('/synthetic-private/credential',8)
    staged=env['OLD']/'operations/verify-native-edits-templates-r1/inputs/STAGED.json'
    put(staged,dict(credential_source=cred),'d0e5d001f50aed7300d19bdcef15ab08e3a8d19bb16bd5a04f9fd1542c24bcd3')
    put(env['OLD']/'TEMPLATE-MANIFEST.json',dict(fixtures=[row]))
    put(env['C']/'ROOT-PROOFS.TEMPLATE.json',dict(selected_manifest=dict(fixtures=[row])))
    put(env['C']/'root_entry.py',{},'a054d39aa563359a6b1e3069d56f7f75c134caaf0d40861f5235752f860b0daa')
    return env,c,files,pins,events,put

def prepared():
    env,c,files,pins,events,put = instance()
    env['prepare'](c)
    return env,c,files,pins,events,put

def executed():
    ctx=prepared();ctx[0]['execute'](ctx[1],1000.0)
    return ctx

check('all_helper_python_compiles_without_execution',lambda:compile(TEXT,str(HELPER),'exec'))
check('exact_two_explicit_flags',lambda:equal(sorted(n.value for n in ast.walk(TREE) if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.startswith('--')), sorted(['--root-reviewed-bind-admit-and-exec','--source-pins-sha256','--bindings','--bindings-sha256','--prepare','--execute-once','--execute-once'])))
check('prepare_full_synthetic_protocol',lambda:prepared())
check('execute_full_synthetic_protocol',lambda:executed())
def copied_review():
    env,c,files,_,events,_=prepared()
    equal(files[str(env['P']/'SOURCE-REVIEW.json')],files[str(env['ACCEPT'])])
    equal([e for e in events if e[0]=='execv'],[])
    equal(any('AUTHORITY' in e[1] or 'FRESH-BOUNDARY' in e[1] for e in events if e[0]=='save'),False)
check('prepare_copies_actual_review_and_no_authority_clock',copied_review)

for field,bad in [('state','ROOT_ACCEPTED_ONE_TEMPLATE_DIAGNOSTIC_SOURCE'),('execution_authority',True),('source_pins_sha256','0'*64),('task24_freeze_sha256','0'*64),('task25_sourcefreeze_sha256','0'*64),('task27_sourcefreeze_sha256','0'*64),('previous_class1_summary_sha256','0'*64),('postchange_purpose','OLD_CLASS1'),('findings_remaining',['unresolved'])]:
    def test(field=field,bad=bad):
        env,c,files,*_=instance();files[str(env['ACCEPT'])][field]=bad
        reject(lambda:env['accepted_review'](c),'EXACT_ROOT_SOURCE_REVIEW')
    check('review_reject_'+field,test)
def review_freeze():
    env,c,files,*_=instance();files[str(env['ACCEPT'])]['source_freeze']['sha256']='0'*64
    reject(lambda:env['accepted_review'](c),'ROOT_REVIEW_FREEZE_JOIN')
check('review_reject_unjoined_source_freeze',review_freeze)

for field in ['execution_closed','parent_absent_or_different_birth','original_and_staged_full_custody_verified']:
    def test(field=field):
        env,c,files,*_=instance();files[str(c.ORIGINAL18_PATH)][field]=False
        reject(lambda:env['history'](c),'OLD18_CLOSED')
    check('history_reject_old18_'+field,test)
for field in ['owned_actor_namespace_unit_and_parent_closed','slot_free','full_original_staged_bank_source_admission_CAS_after_closure']:
    def test(field=field):
        env,c,files,*_=instance();files[str(env['PREVIOUS'])][field]=False
        reject(lambda:env['history'](c),'CLASS1_CLOSED')
    check('history_reject_class1_'+field,test)
for field in ['ROOT-BINDINGS.json','FRESH-BOUNDARY.json','RUNTIME-AUTHORITY.json']:
    def test(field=field):
        env,c,_,_,_,put=prepared();put(env['P']/field,{})
        reject(lambda:env['execute'](c,1000.0),'NEW_OPERATION_ALREADY_STARTED_NO_REPLAY')
    check('consumed_reject_'+field,test)
for suffix in ['.ADMISSION.json','.ENTRY-INTENT.json']:
    def test(suffix=suffix):
        env,c,_,_,_,put=prepared();put(env['C']/(env['KEY']+suffix),{})
        reject(lambda:env['execute'](c,1000.0),'NEW_OPERATION_ALREADY_STARTED_NO_REPLAY')
    check('consumed_reject_'+suffix,test)

def assemble_protocol():
    env,c,files,pins,events,put=executed()
    aenv=dict(require=need)
    etree=ast.parse(ETEXT)
    fn=next(n for n in etree.body if isinstance(n,ast.FunctionDef) and n.name=='assemble')
    # Replace only local import with the exact synthetic contract constants.
    fn.body=[n for n in fn.body if not isinstance(n,ast.ImportFrom)]
    aenv.update({k:getattr(c,k) for k in ['ASSIGNMENT','MODE','SELECTED_ID','LIMITS']})
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'<synthetic-root-entry-assemble>','exec'),aenv)
    bound=files[str(env['P']/'ROOT-BINDINGS.json')]
    admission=aenv['assemble'](bound,env['SOURCE_SHA'],uid=1000,boot='synthetic-boot',now=env['now'](),monotonic_now=1000.0)
    c.diagnostic_acceptance(admission)
    renv=dict(c=c,need=need,Path=env['Path'],os=env['os'],time=env['time'],re=re,proof=c.runtime_pin_check,fresh_time=lambda value,code:equal(value,env['now']()))
    extract(RTEXT,{'validate_fields'},renv)
    renv['validate_fields'](admission)
    return env,c,files,admission,renv,aenv
check('actual_extracted_entry_contract_and_rootframe_full_protocol',assemble_protocol)
for field in ['assignment','operation_key','source_pins_sha256','task27_sourcefreeze_sha256','previous_class1_summary_sha256','postchange_purpose','selected_manifest','source_review','original18_closure','fresh_boundary']:
    def test(field=field):
        env,c,files,a,_,_=assemble_protocol()
        files[a['runtime_authority']['path']][field]='INVALID'
        reject(lambda:c.diagnostic_acceptance(a),'ROOT_RUNTIME_EXACT_JOINS')
    check('authority_reject_exact_join_'+field,test)
for field,bad in [('original18_replayed',True),('previous_class1_replayed',True),('actual_normal_payload_type_before','KNOWN'),('original_strict_all_pass',True),('whole_F06_accepted',True),('max_document_loads',True),('max_getRequest_calls',2),('stores',1),('correct_password_only',False),('limits',{})]:
    def test(field=field,bad=bad):
        env,c,files,a,_,_=assemble_protocol();files[a['runtime_authority']['path']][field]=bad
        reject(lambda:c.diagnostic_acceptance(a),'ROOT_SINGLE_OBSERVATION_AUTHORITY')
    check('authority_reject_scope_'+field,test)
for field in ['boot_id','nonce','original_operation_start_monotonic']:
    def test(field=field):
        env,c,files,a,_,_=assemble_protocol();files[a['runtime_authority']['path']][field]='INVALID'
        reject(lambda:c.diagnostic_acceptance(a),'ROOT_AUTHORITY_CURRENT_CLOCK_SCOPE')
    check('authority_reject_clock_'+field,test)
for field,bad in [('state','OLD_FRESH_STATE'),('nonce','INVALID'),('bank',{}),('affinity_cpu_ids',[0,1]),('memory_available_kib',1),('CPU_pressure_raw',''),('IO_pressure_raw',''),('prior_operation_closed',False),('shared_slot_free_observed',False),('selected_ciphertext',{}),('credential_metadata',{})]:
    def test(field=field,bad=bad):
        env,c,files,a,r,_=assemble_protocol();files[a['fresh_boundary']['path']][field]=bad
        reject(lambda:r['validate_fields'](a))
    check('fresh_reject_'+field,test)

def deterministic_json():
    fn=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='save')
    assignment=next(n for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='raw' for t in n.targets))
    code=compile(ast.Expression(body=assignment.value),'<synthetic-serialization>','eval')
    equal(eval(code,dict(json=json,value={'z':'ю','a':2})),eval(code,dict(json=json,value={'a':2,'z':'ю'})))
check('stable_proof_serialization_across_dict_order',deterministic_json)

def source_pin_control(bad=None):
    env,c,files,pins,events,put=instance()
    rows=[]
    for i in range(60):
        p=env['T']/('synthetic-source-'+str(i));r=put(p,{},size=10);rows.append({k:r[k] for k in ['path','bytes','sha256']})
    put(env['C']/'SOURCE-PINS.json',{},env['SOURCE_SHA'])
    put(env['T']/'SOURCE-FREEZE.json',dict(files=rows),env['FREEZE_SHA'])
    def imported(spec):events.append(('candidate_import',spec));return c
    env['importlib']=types.SimpleNamespace(util=types.SimpleNamespace(spec_from_file_location=lambda name,path:types.SimpleNamespace(loader=types.SimpleNamespace(exec_module=lambda m:events.append(('exec_module','synthetic-contract')))),module_from_spec=imported))
    if bad=='pin':pins[str(env['C']/'SOURCE-PINS.json')]['sha256']='0'*64
    if bad=='freeze':pins[str(env['T']/'SOURCE-FREEZE.json')]['sha256']='0'*64
    if bad=='body':pins[rows[-1]['path']]['sha256']='0'*64
    if bad=='accept':pins[str(env['ACCEPT'])]['sha256']='0'*64
    if bad:
        reject(lambda:env['source']())
        equal(any(x[0]=='candidate_import' for x in events),False)
    else:
        env['source']()
        equal(sum(x[0]=='candidate_import' for x in events),1)
check('all_sixty_source_pins_before_candidate_import',source_pin_control)
for label in ['pin','freeze','body','accept']:
    check('source_drift_reject_before_import_'+label,lambda label=label:source_pin_control(label))

result=dict(schema='friday.source-only.caller-controls.v1',state='PASS' if all(r['passed'] for r in ROWS) else 'FAIL',
    helper_sha256=hashlib.sha256(TEXT.encode()).hexdigest(),checks=len(ROWS),passed=sum(r['passed'] for r in ROWS),observations=ROWS,
    boundary='Only source text/AST and in-memory fake filesystem/proofs/resources. No helper/candidate imports, real custody, credential/doc bodies, grants, clocks or live effects.',
    synthetic_protocol_includes='Full prepare->execute builders, extracted accepted root_entry.assemble/f06_contract.manifest_contract/diagnostic_acceptance/output_inputs/root_frame.validate_fields; no variable/name/API joins skipped.')
raw=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode()
out=HERE/'SOURCE-PROTOCOL-CONTROLS.json'
out.write_bytes(raw);out.chmod(0o600)
print(json.dumps({k:v for k,v in result.items() if k!='observations'},sort_keys=True))
if result['state']!='PASS':
    print(json.dumps([r for r in ROWS if not r['passed']],indent=2))
    raise SystemExit(1)
