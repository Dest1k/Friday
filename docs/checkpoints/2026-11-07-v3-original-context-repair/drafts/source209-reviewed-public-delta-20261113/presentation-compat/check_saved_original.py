"""Bounded saved-only consumer checks. Never Store/current/API/credential effects.

All saved JSON and original artifact bytes stay in RAM; only hashes, names,
counts, enum errors and check booleans are persisted. Scope intentionally
omits global current inventory: Root must separately run the complete caller.
"""
from pathlib import Path, PosixPath
import ast, copy, datetime as dt, hashlib, json, os, resource, types
OUT=Path(__file__).parent
OLD=Path('/home/jericho/.cache/FRW-SOL-V3-PRESENTATION-CURRENT209-CALLER-CORE-20261113')
UNIT=Path('/home/jericho/.cache/FRW-ASTRA-SOL-T38-PRESENTATION-CURRENT209-CALLER-20261113/ROOT-V03-RETAINED-ORIGINAL-UNIT-BOUND.json')
COMPOSED=Path('/home/jericho/.cache/FRW-ASTRA-V3-PRESENTATION-ORDINARY209-ROOT-20261113/revision2/DIAGNOSTIC-GENUINE-ORDINARY-SOURCE.py')
for key,val in [(resource.RLIMIT_CPU,60),(resource.RLIMIT_AS,768*1024**2),(resource.RLIMIT_FSIZE,8*1024**2)]:resource.setrlimit(key,(val,val))
def sha(raw):return hashlib.sha256(raw).hexdigest()
def ref(path):
 raw=Path(path).read_bytes();return dict(path=str(path),bytes=len(raw),sha256=sha(raw))
def load(path):
 raw=path.read_bytes();m=types.ModuleType('_saved_consumer');m.__file__=str(path);exec(compile(raw,str(path),'exec'),m.__dict__);return m
p=load(OUT/'presentation_prepare.py');old=load(OLD/'presentation_prepare.py')
assert ref(UNIT)==dict(path=str(UNIT),bytes=2815,sha256='a186844cddf35fc54e63b63fc7c778c82a40988dca2cd06c54de82d53aa45525')
u=json.loads(UNIT.read_bytes());source=json.loads(Path(u['original']['run']['path']).read_bytes());root=Path(u['original']['run']['path']).parent.parent
admission=json.loads(Path(u['original']['admission']['path']).read_bytes());plan=admission['plan'];rid=source['id']
g=load(COMPOSED);safe=g.safe_read;cache={};reads=[]
# Bounded read policy allows only original and immediate linked metadata.
allowed={Path(r['path']) for r in u['original'].values() if isinstance(r,dict) and 'path' in r}|{Path(u['Root_binding']['path'])}
allowed|={root/'runs'/(plan['predecessor']['run_id']+'.json'),root/plan['predecessor']['admission_reference']['basename']}
allowed|={root/source['sent_task_reference']['basename']}
allowed|={root/'updates'/(str(uid)+suffix) for uid in source['seen'] for suffix in ('.json','.arrival.json')}
for o in source['observations']:
 for k in ('receipt_path','path'):
  if k in o:allowed.add(Path(o[k]))
 allowed.add(Path(o['path']).with_suffix('.overflow.json')) if 'path' in o else None

def bounded_read(path,*args,**kwargs):
 path=Path(path)
 permitted=(path in allowed or (path.parent==root and
  (path.name.startswith('receive-'+rid+'-0-1-') or path.name=='terminal-response-'+rid+'-0-1.json')))
 if not permitted:raise AssertionError('SAVED_SCOPE_READ_REFUSED:'+path.name)
 if path not in cache:cache[path]=safe(path,*args,**kwargs)
 reads.append(path);return cache[path]
g.safe_read=bounded_read
# The genuine historical explicit-cursor branch consumes the exact cursor
# retained by the original's deterministic immediate successor admission.
key=g.digest(g.encoded(dict(admission=source['continuation_reference'],task=source['sent_task_reference'],ack=source['sent_api_ack_reference'],window=source['sent_window_reference'])))
successor_path=root/('continue-'+key+'.json');allowed.add(successor_path)
succ=json.loads(bounded_read(successor_path));pin=succ['plan']['predecessor'];cursor=succ['predecessor_cursor']
assert succ['schema']=='friday.tester.closed-unknown-admission.v1' and succ['plan_sha256']==g.digest(g.encoded(succ['plan']))
assert pin['run_id']==rid and pin['run_sha256']==p.SOURCE_REF['run_sha256'] and pin['admission_reference']==source['continuation_reference']
assert pin['cursor_sha256']==g.digest(g.encoded(cursor)) and cursor['capture_receipts'][g.Runner.receive_key(None,source)]==source['receive_head']

class ScopedRoot(PosixPath):
 def glob(self,pattern):
  if self==root and pattern=='continue-*.json':return iter([Path(u['original']['admission']['path'])])
  if self==root and pattern.startswith('receive-'+rid+'-0-1-'):return Path(self).glob(pattern)
  raise AssertionError('SAVED_SCOPE_GLOB_REFUSED')
class ReadOnlyStore:
 def __init__(self):
  self.root=ScopedRoot(root);self.downloads=root/'downloads';self.captures=root/'updates'
 def get(self,path):return json.loads(bounded_read(path),object_pairs_hook=g.unique_object)
 def run_path(self,run_id):
  if run_id not in (rid,plan['predecessor']['run_id']):raise AssertionError('SAVED_SCOPE_RUN_REFUSED')
  return self.root/'runs'/(run_id+'.json')
 def __getattr__(self,name):raise AssertionError('SAVED_STORE_WRITE_OR_OTHER_REFUSED:'+name)
class SavedRunner(g.Runner):
 # A historical-cursor call adapter, never a replacement verifier. Both outer
 # terminal check and nested verify_reply_custody call the genuine method.
 def receive_inventory(self,run,cursor_arg=None,terminal=False):
  assert run['id']==rid
  return g.Runner.receive_inventory(self,run,cursor if cursor_arg is None else cursor_arg,terminal)

def runner():
 r=SavedRunner(ReadOnlyStore(),None,clock=lambda:source['deadline']+1,sleep=lambda *_:(_ for _ in ()).throw(AssertionError('NO_SLEEP')))
 r._presentation_reference_bytes=lambda reference:bounded_read(reference['path'])
 return r
checks=[]
def yes(name,body):
 body();checks.append(dict(name=name,status='PASS'))
def refuses(name,body,enum=None):
 try:body()
 except (ValueError,g.Refused,AssertionError) as e:
  code=str(e)
  assert enum is None or code==enum,(name,type(e).__name__,code)
  checks.append(dict(name=name,status='PASS',exception_class=type(e).__name__,enum=code if (code.startswith('PRESENTATION_') or code in ('Successor requires the exact full-window closed admitted ACK/capture','Bounded reply window commitment custody mismatch','Capture receipt exact bytes/hash changed','Reply artifact bytes/raw custody changed after receipt')) else None));return
 raise AssertionError('EXPECTED_REFUSAL:'+name)

refuses('exact_original_serial_predecessor_seam_reproduced',lambda:g.Runner.serial_predecessor(runner(),plan),'Successor requires the exact full-window closed admitted ACK/capture')
r=runner();before=set(r.__dict__);answer=p.validate_original_runner(r,u);assert answer['state']=='ORIGINAL_UPLOAD_UNIT_AUTHENTICATED_NOT_NEW_EFFECT_GRANT' and set(r.__dict__)==before
checks.append(dict(name='actual_saved_original_genuine_full_custody_window_terminal_chain',status='PASS'))
r=runner();sentinel=('other-run',{'must':'restore'});r._closed_text_predecessor=sentinel;r.reply_run={'restore':True};p.validate_original_runner(r,u);assert r._closed_text_predecessor is sentinel and r.reply_run=={'restore':True}
checks.append(dict(name='success_restores_preexisting_runner_scope',status='PASS'))

for name,edit,enum in [
 ('altered_original_alias_refused',lambda x:x.update(original_alias=x['original_alias'].replace('02f210','7343aa')),'PRESENTATION_EXACT_V03_RETAINED_UNIT_REQUIRED'),
 ('altered_source_SHA_refused',lambda x:x['current_source'].update(sha256='a'*64),'PRESENTATION_ORIGINAL_ALIAS_AND_SOURCE_CAS_REQUIRED'),
 ('altered_original_run_pin_refused',lambda x:x['original']['run'].update(sha256='a'*64),'PRESENTATION_ORIGINAL_UPLOAD_RECEIPT_UNIT_REQUIRED'),
]:
 value=copy.deepcopy(u);edit(value);refuses(name,lambda:p.validate_original_runner(runner(),value),enum)

# Changed unit/ref and Root-binding bytes are internally consistent in RAM;
# semantic joins must still reject the altered original admission or closure.
def changed_unit(key,edit):
 value=copy.deepcopy(u);data=json.loads(bounded_read(value['original'][key]['path']));edit(data);raw=p.encoded(data);value['original'][key].update(bytes=len(raw),sha256=p.digest(raw))
 rootdata=json.loads(bounded_read(value['Root_binding']['path']));rootdata['original']=value['original'];rootraw=p.encoded(rootdata);value['Root_binding'].update(bytes=len(rootraw),sha256=p.digest(rootraw))
 r=runner();r._presentation_reference_bytes=lambda z:rootraw if z['path']==value['Root_binding']['path'] else raw if z['path']==value['original'][key]['path'] else bounded_read(z['path'])
 return r,value
r,v=changed_unit('admission',lambda d:d['plan'].update(new_run_id='different-original'))
refuses('reissued_unit_cannot_substitute_admission',lambda:p.validate_original_runner(r,v),'PRESENTATION_ORIGINAL_EXACT_ADMISSION_REFERENCE_REQUIRED')
for name,edit in [('closure_resource0',lambda d:d.update(resource0=False)),('closure_full180',lambda d:d.update(full180=False)),('closure_run',lambda d:d['run'].update(sha256='a'*64)),('closure_replayed',lambda d:d.update(original_replayed=True)),('closure_child_not_reaped',lambda d:d['child_reaped'].update(reaped=False))]:
 r,v=changed_unit('closed_operation',edit);refuses(name+'_refused',lambda:p.validate_original_runner(r,v),'PRESENTATION_ORIGINAL_FULL_WINDOW_OPERATIONAL_CLOSURE_REQUIRED');assert not hasattr(r,'_closed_text_predecessor')

# Actual genuine window and receive-chain bytes tampering after pinned unit
# reads is rejected inside the original consumer, with temporary scope restored.
for name,path,enum in [
 ('genuine_window_tamper',root/source['sent_window_reference']['basename'],'Bounded reply window commitment custody mismatch'),
 ('genuine_terminal_head_tamper',root/source['receive_head']['basename'],'Capture receipt exact bytes/hash changed')]:
 raw=bounded_read(path);r=runner();r._presentation_reference_bytes=lambda z:raw if z['path']==str(path) else bounded_read(z['path']);cache[path]=raw+b' '
 try:refuses(name+'_refused',lambda:p.validate_original_runner(r,u),enum);assert not hasattr(r,'_closed_text_predecessor') and not hasattr(r,'reply_run')
 finally:cache[path]=raw

# The scope is only for verifying the original receipt. A direct predecessor
# request still enters genuine serial_predecessor and retains the same refusal.
r=runner();r._closed_text_predecessor=(rid,plan)
refuses('original_scope_does_not_reauthorize_consumed_predecessor',lambda:g.Runner.serial_predecessor(r,plan),'Successor requires the exact full-window closed admitted ACK/capture')

# Exact source methods preserve future whole-prefix, ACK10, cancel, once and
# current guards: composition itself remains byte-for-byte identical for the
# same actual Root phase/authority. Compare all unaffected source AST nodes.
def defs(path):
 t=ast.parse(path.read_bytes());return {n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a,b=defs(OLD/'presentation_prepare.py'),defs(OUT/'presentation_prepare.py');assert set(a)==set(b)
assert {k for k in a if a[k]!=b[k]}=={'validate_original_runner'}
assert (OLD/'root_presentation_once.py').read_bytes()==(OUT/'root_presentation_once.py').read_bytes()
assert (OLD/'presentation_postconditions.py').read_bytes()==(OUT/'presentation_postconditions.py').read_bytes()
a=ast.parse((OLD/'presentation_current209.py').read_bytes());b=ast.parse((OUT/'presentation_current209.py').read_bytes())
for tree in (a,b):tree.body=[n for n in tree.body if not (isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='PREP' for x in n.targets))]
assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
checks.append(dict(name='all_NEW_SEND_wholeprefix_cancel_current_permission_CAS_once_ACK10_resources_source_unchanged',status='PASS'))
checker=load(OUT/'presentation_current209.py');assert checker.PREP==ref(OUT/'presentation_prepare.py')
checks.append(dict(name='checker_exact_new_PREP_pin_propagated',status='PASS'))
for name in ('presentation_prepare.py','presentation_current209.py','root_presentation_once.py','presentation_postconditions.py'):compile((OUT/name).read_bytes(),str(OUT/name),'exec')
checks.append(dict(name='all_four_sources_compile_without_pycache',status='PASS'))
result=dict(schema='frw.presentation.original-receipt.saved-consumer-checks.v1',state='SOURCE_SAVED_ONLY_NOT_CURRENT_OR_EFFECT_QUALIFICATION',completed_moscow=dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).isoformat(),checks=checks,count=len(checks),failures=[],original_unit=ref(UNIT),genuine_composed_source=ref(COMPOSED),historical_cursor_basis=ref(successor_path),source_refs=[ref(OUT/name) for name in ('presentation_prepare.py','presentation_current209.py','root_presentation_once.py','presentation_postconditions.py')],saved_metadata_files_read=len(set(reads)),saved_metadata_bytes=sum(len(cache[x]) for x in set(reads)),global_current_cursor_reads=0,credential_reads=0,Store_constructors=0,API_clients=0,model_requests=0,send_calls=0,current_collections=0,remaining='Root must bind new four-source review/checker/driver refs and run complete actual realStore whole-prefix/current readonly before any claim/clock/API/new/send. Saved cursor adapter is not a current authority.',no_document_bodies_persisted=True)
(OUT/'SAVED-ORIGINAL-CHECKS.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');(OUT/'SAVED-ORIGINAL-CHECKS.json').chmod(0o600)
print(json.dumps(dict(checks=len(checks),failures=0,actual_saved_original='PASS',global_current_reads=0,Store_constructors=0,API_clients=0)))
