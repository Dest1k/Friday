"""Independent AST-only controls. No gdb import or inferior/runtime execution."""
from pathlib import Path
from types import SimpleNamespace
import ast, copy, difflib, hashlib, json, time
ROOT = Path('/home/jericho/.cache/FRW-ASTRA-CALC-OFFICE-LOAD-NEW-FORK-SOURCE-SCOPE-20261115')
BASE = ROOT/'before/native_return_observer.py'
CANDIDATE = ROOT/'candidate/native_return_observer.py'
HELPER = Path('/home/jericho/.cache/FRW-ASTRA-CALC-GDB-OFFICE-CORE-DIAGNOSIS-20261115/candidate/paper_helper_gdb.py')
PINS = {BASE:'4eb25d42b9487b151d9014771d25b2eb19878410c58d748aa19b0187c9c9fd29',
        CANDIDATE:'6c3b9d5c2d70db950a16982654a3f02f2790488db1ab1153e0f966e305f358c3',
        HELPER:'6c7f293cb7636b34f747143b797f9e6601d96d83ff5e49a752446bbfff334b10'}
checks=[]
def check(name, fn):
    fn()
    checks.append({'name':name,'state':'PASS'})
def req(v, reason='control_failed'):
    if not v: raise AssertionError(reason)
for path,pin in PINS.items(): req(hashlib.sha256(path.read_bytes()).hexdigest()==pin, str(path))
old,new = BASE.read_text(),CANDIDATE.read_text()
ot,nt = ast.parse(old),ast.parse(new)
def patch_exact():
    patch=''.join(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),
              fromfile='before/native_return_observer.py',tofile='candidate/native_return_observer.py'))
    req(patch==(ROOT/'source-delta.patch').read_text())
    lines=patch.splitlines(keepends=True)
    # Reconstruct the single hunk against exact old bytes, validating every context line.
    import re
    h=next(i for i,l in enumerate(lines) if l.startswith('@@'))
    m=re.fullmatch(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@\n',lines[h]);req(m)
    old_lines=old.splitlines(keepends=True);start=int(m[1])-1;pos=start;result=old_lines[:start]
    added=removed=0
    for line in lines[h+1:]:
        if line[0] in ' -': req(old_lines[pos]==line[1:]);pos+=1
        if line[0] in ' +': result.append(line[1:])
        if line[0]=='+': added+=1
        if line[0]=='-': removed+=1
    result+=old_lines[pos:]
    req(''.join(result)==new and added==8 and removed==0)
check('exact_patch_reconstruction_eight_added_lines',patch_exact)
def ast_scope():
    od={n.name:ast.dump(n) for n in ot.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    nd={n.name:ast.dump(n) for n in nt.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    req(od.keys()==nd.keys() and [k for k in od if od[k]!=nd[k]]==['stopped'])
    req(ast.dump(ast.Module(body=[n for n in ot.body if not isinstance(n,(ast.FunctionDef,ast.ClassDef))],type_ignores=[]))
        ==ast.dump(ast.Module(body=[n for n in nt.body if not isinstance(n,(ast.FunctionDef,ast.ClassDef))],type_ignores=[])))
check('all_other_functions_classes_and_top_level_unchanged',ast_scope)
def extract(tree,names,ns):
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    req({n.name for n in nodes}==set(names))
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<independent-extracted-only>','exec'),ns)
    return ns
adapter=next(n for n in ast.parse(HELPER.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='Adapter')
hns={'require':lambda v,reason: None if v else (_ for _ in ()).throw(RuntimeError(reason))}
extract(ast.Module(body=adapter.body,type_ignores=[]),['boundary','dispatch'],hns)
class SignalEvent: pass
class BreakpointEvent:
    def __init__(self, nums): self.breakpoints=[SimpleNamespace(number=n,type=7) for n in nums]
class H:
    def __init__(self,ns,error=None,prior_pending=None):
        self.n=ns;self.g=ns['gdb'];self.catchpoints={1:'fork',2:'vfork',3:'exec'}
        self.pending=prior_pending;self.pending_stop='stale_stop';self.to_create=['stale_creation'];self.actions=[];self.error=error
    def queue_stop(self,event): return False
    def boundary(self,event):
        if self.error is not None: raise self.error
        return hns['boundary'](self,event)
    def birth(self): self.actions.append('birth')
    def exec(self): self.actions.append('exec')
    def publish(self): self.actions.append('publish')
def env(error=None,prior=None,pending=None):
    calls=[];saves=[]
    ns={'STATE':{'error':prior,'status':'READY','process':None},'pending_action':pending,
        'gdb':SimpleNamespace(SignalEvent=SignalEvent,BreakpointEvent=BreakpointEvent,BP_CATCHPOINT=7)}
    ns['save']=lambda:saves.append(copy.deepcopy(ns['STATE']))
    ns['process_boundary_snapshot']=lambda:(calls.append('snapshot') or {'schema':'frw.process-boundary-symbols.v1','frames':[]})
    extract(nt,['stopped','fail'],ns);ns['helper']=H(ns,error=error,prior_pending=pending)
    return ns,calls,saves
for name,nums in [('unknown_catchpoint_number',[999]),('multiple_accepted_catchpoints',[2,3]),('mixed_fork_vfork',[1,2])]:
    def run(nums=nums):
        ns,calls,saves=env();ns['stopped'](BreakpointEvent(nums))
        req(calls==['snapshot'] and ns['helper'].actions==[] and ns['helper'].pending is None)
        req(ns['pending_action'] is None and ns['STATE']['error']=='helper_unexpected_fork_or_catchpoint')
        req(ns['STATE']['status']=='REFUSED' and saves[-1]==ns['STATE'])
    check(name+'_still_refused_without_continue',run)
def subclass_and_prefix():
    class RefusalSubclass(RuntimeError): pass
    for error,reason in [(RefusalSubclass('helper_unexpected_fork_or_catchpoint'),'RefusalSubclass'),
                         (RuntimeError('helper_unexpected_fork_or_catchpoint_extra'),'helper_unexpected_fork_or_catchpoint_extra')]:
        ns,calls,saves=env(error=error);ns['stopped'](BreakpointEvent([1]))
        req(calls==[] and ns['STATE']['error']==reason and len(saves)==1)
check('exact_type_and_exact_identifier_gate',subclass_and_prefix)
def real_helper_prior_error():
    ns,calls,saves=env(prior='original_first_error');ns['STATE']['process_boundary_diagnostic']={'retained':True}
    ns['stopped'](BreakpointEvent([1]))
    req(calls==[] and saves==[] and ns['STATE']['error']=='original_first_error')
    req(ns['STATE']['process_boundary_diagnostic']=={'retained':True} and ns['helper'].actions==[])
check('exact_helper_prior_error_short_circuits_without_overwrite',real_helper_prior_error)
def stale_pending_is_terminal():
    ns,calls,saves=env(pending='CONTINUE');ns['stopped'](BreakpointEvent([1]))
    # No new action is enqueued. Existing helper dispatch drops its prior pending work on refusal.
    req(ns['STATE']['error']=='helper_unexpected_fork_or_catchpoint')
    req(hns['dispatch'](ns['helper']) is None)
    req(ns['helper'].pending is None and ns['helper'].pending_stop is None and ns['helper'].to_create==[])
    # Native main's mandatory error check precedes dispatch and the next loop continuation.
    main=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    loop=next(n for n in main.body if isinstance(n,ast.While))
    req(isinstance(loop.body[0],ast.Expr) and ast.unparse(loop.body[0].value).startswith("gdb.execute('continue'"))
    req(ast.unparse(loop.body[1])=="require(STATE['error'] is None, 'trace_refused')")
    req('helper.dispatch()' in ast.unparse(loop.body[2]))
check('prior_pending_actions_cannot_cross_main_error_gate',stale_pending_is_terminal)
def metadata_failures_no_content():
    class F:
        def is_valid(self):return True
        def pc(self):return 42
        def type(self):return 0
        def name(self):return None
        def older(self):raise ValueError('PRIVATE_DOCUMENT_CONTENT')
    def fail_identity(): raise OSError('PRIVATE_ENV_AND_PATH')
    ns={'gdb':SimpleNamespace(inferiors=fail_identity,newest_frame=lambda:F(),solib_name=lambda pc:None),
        'Path':Path,'STATE':{'process':None},'os':SimpleNamespace(getpid=lambda:99)}
    extract(nt,['boundary_symbol','process_boundary_snapshot'],ns)
    result=ns['process_boundary_snapshot']()
    req(result['frames']==[{'pc':42,'kind':0,'symbol':None,'module_basename':None}])
    req(result['identity_exception_class']=='OSError' and result['stack_exception_class']=='ValueError')
    req('PRIVATE' not in json.dumps(result) and 'frames_truncated' not in result)
check('unresolved_frames_and_unwind_failures_are_not_fabricated',metadata_failures_no_content)
def snapshot_allowed_apis():
    fn=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name=='process_boundary_snapshot')
    calls={ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n,ast.Call)}
    req(not any(s in calls for s in ['gdb.execute','gdb.parse_and_eval','gdb.write_memory','gdb.selected_frame','gdb.Frame.read_register']))
    req({s for s in calls if s.startswith('gdb.')}=={'gdb.inferiors','gdb.selected_inferior','gdb.selected_thread','gdb.newest_frame','gdb.solib_name'})
    req({s for s in calls if s.startswith('f.')}=={'f.read','f.is_valid','f.pc','f.type','f.name','f.older'})
check('snapshot_has_no_commands_expression_register_or_value_apis',snapshot_allowed_apis)
print(json.dumps({'schema':'frw.office-fork-independent-source-controls.v1','state':'PASS_SOURCE_ONLY',
                  'checks':checks,'count':len(checks),'forbidden_effects_executed':False,
                  'limit':'AST-extracted exact code over synthetic metadata only. No GDB import, /proc read, Office, inferior, helper process or model.'},indent=2))
