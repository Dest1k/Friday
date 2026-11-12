"""Synthetic Python controls only. No UNO/native/runtime/application imports."""
import ast, contextlib, gc, hashlib, io, json, pathlib, sys, types
B=pathlib.Path(__file__).resolve().parent
# Read only exact source and metadata, all before the test audit boundary.
source={n:(B/'candidate'/n).read_text() for n in ('request_args_compat_v2.py','conversion_probe.py','callback_observer_v2.py','readonly_diagnostic.py','diagnostic_client.py')}
uno_text=(B/'baseline/uno.py').read_text()
old_source=(B/'baseline/request_args_compat_v2.py').read_text()
actual=json.loads(pathlib.Path('/home/jericho/.cache/FRW-SOL-V3-F06-ONE-TEMPLATE-DIAGNOSTIC-FRAME-20261112/candidate/operations/one-template-diag-class1/work/one-template-diagnostic/RESULT.json').read_bytes())
# All later file/process/network/credential access is forbidden. No fake native admission.
def audit(event,args):
    if event in ('open','os.system','subprocess.Popen','os.fork','os.posix_spawn') or event.startswith('socket.'):
        raise RuntimeError('PURE_AUDIT_REFUSED')
sys.addaudithook(audit)
modules={}
for name in ('request_args_compat_v2','conversion_probe','callback_observer_v2','readonly_diagnostic'):
    m=types.ModuleType(name);exec(compile(source[name+'.py'],name+'.py','exec'),m.__dict__);modules[name]=m;sys.modules[name]=m
c=modules['request_args_compat_v2'];probe_mod=modules['conversion_probe'];cb=modules['callback_observer_v2'];ad=modules['readonly_diagnostic']
old={};exec(compile(old_source,'baseline_compat.py','exec'),old)
node=next(n for n in ast.parse(uno_text).body if isinstance(n,ast.FunctionDef) and n.name=='_uno_struct__setattr__')
ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'uno.py','exec'),ns);original=ns['_uno_struct__setattr__']
checks=[]
def ok(name,value):
    assert value,name
    checks.append({'name':name,'pass':True})
def raises(cls, fn):
    try:fn()
    except cls as e:return e
    raise AssertionError('EXPECTED_FIXED_EXCEPTION')
SECRET='SYNTHETIC_PRIVATE_VALUE_NEVER_LOGGED'
class Fields:
    __slots__=('calls','Message','Context','ErrCode')
    def __init__(self):object.__setattr__(self,'calls',[])
    def __setattr__(self,name,value):
        self.calls.append(name)
        if name=='ErrCode' and type(value) is not int:raise TypeError('FIXED_TYPED_FIELD')
        if name=='Message' and type(value) is not str:raise TypeError('FIXED_TYPED_FIELD')
        object.__setattr__(self,name,value)
def init(self, fields):self.__dict__['value']=fields
class U:
    def __init__(self):
        self._uno_struct__setattr__=original;self.classes={};self.requests=[]
        for name in c.REQUEST_NAMES:
            parent=(self.classes.get('com.sun.star.task.ErrorCodeRequest',Exception) if name.endswith('ErrorCodeRequest2') else Exception)
            self.classes[name]=type(name,(parent,),{'__pyunostruct__':name,'__init__':init,'__setattr__':original})
    def getClass(self,name):self.requests.append(name);return self.classes[name]
def obj(u,name=None):
    f=Fields();cls=u.classes[name or c.REQUEST_NAMES[-1]];return cls(f),f
# Direct extracted real uno.py setter reproduces actual AttributeError, not a live C++ conversion.
u=U();x,f=obj(u);e=raises(AttributeError,lambda:setattr(x,'args',(SECRET,)))
ok('baseline_real_uno_setter_AttributeError_reproduced',type(e) is AttributeError and f.calls==['args'])
# Old exact-five helper still fails observed sixth. Its five classes restore in finally.
t=old['install_request_args_compat'](u)
try:ok('old_five_leaves_observed_sixth_failing',type(raises(AttributeError,lambda:setattr(x,'args',(SECRET,)))) is AttributeError)
finally:old['restore_request_args_compat'](t)
# Correct native hierarchy built before installation: ErrorCodeRequest2 derives ErrorCodeRequest.
u=U();u.classes[c.REQUEST_NAMES[4]]=type(c.REQUEST_NAMES[4],(u.classes[c.REQUEST_NAMES[5]],),{'__pyunostruct__':c.REQUEST_NAMES[4],'__init__':init,'__setattr__':original})
helper0=u._uno_struct__setattr__;factory0=type(u).getClass;t=c.install_request_args_compat(u)
try:
    for name in c.REQUEST_NAMES:
        x,f=obj(u,name);setattr(x,'args',(SECRET,));ok('exact_reserved_args_'+name.rsplit('.',1)[1],BaseException.args.__get__(x)==(SECRET,) and f.calls==[])
        for field,value in [('Message',SECRET),('Context',object()),('ErrCode',283)]:setattr(x,field,value)
        ok('original_field_delegation_once_'+name.rsplit('.',1)[1],f.calls==['Message','Context','ErrCode'])
        error=raises(TypeError,lambda:setattr(x,'ErrCode',SECRET));ok('typed_ErrCode_refusal_'+name.rsplit('.',1)[1],type(error) is TypeError and f.calls[-1]=='ErrCode')
    x,f=obj(u)
    for value in ([SECRET],SECRET,None,iter([SECRET])):
        before=list(f.calls);error=raises(TypeError,lambda:setattr(x,'args',value));ok('invalid_args_'+type(value).__name__,str(error)=='password_request_args_tuple_required' and before==f.calls)
    class TupleSubclass(tuple):pass
    raises(TypeError,lambda:setattr(x,'args',TupleSubclass()))
    ok('tuple_subclass_refused_preserves_previous_contract',True)
    subclass=type('UnlistedSubclass',(u.classes[c.REQUEST_NAMES[-1]],),{})
    y=subclass(Fields());ok('unlisted_subclass_delegates_strict_original',type(raises(AttributeError,lambda:setattr(y,'args',(SECRET,)))) is AttributeError)
    alien=type('AlienException',(Exception,),{'__init__':init,'__setattr__':t[-1][2]})
    y=alien(Fields());ok('copied_setter_on_other_exception_delegates',type(raises(AttributeError,lambda:setattr(y,'args',(SECRET,)))) is AttributeError)
    struct=type('OrdinaryStruct',(),{'__init__':init,'__setattr__':original});y=struct(Fields());ok('ordinary_struct_args_still_strict',type(raises(AttributeError,lambda:setattr(y,'args',(SECRET,)))) is AttributeError)
    unknown=type('com.sun.star.task.UnknownRequest',(Exception,),{'__pyunostruct__':'com.sun.star.task.UnknownRequest','__init__':init,'__setattr__':original});y=unknown(Fields());ok('unknown_generated_exception_unchanged',type(raises(AttributeError,lambda:setattr(y,'args',(SECRET,)))) is AttributeError)
    ok('global_helper_and_factory_never_patched',u._uno_struct__setattr__ is helper0 and type(u).getClass is factory0)
    ok('double_install_refused_without_partial_mutation',type(raises(ValueError,lambda:c.install_request_args_compat(u))) is ValueError and all(cls.__dict__['__setattr__'] is replacement for cls,_,replacement in t))
finally:c.restore_request_args_compat(t)
ok('all_six_setters_restored',all(cls.__dict__['__setattr__'] is original for cls in u.classes.values()))
# Validation completes before any setter writes.
for problem in ('alias','wrong_name','not_exception','foreign_setter'):
    u=U();key=c.REQUEST_NAMES[-1];cls=u.classes[key]
    if problem=='alias':u.classes[key]=u.classes[c.REQUEST_NAMES[0]]
    if problem=='wrong_name':cls.__pyunostruct__='com.sun.star.task.Wrong'
    if problem=='not_exception':u.classes[key]=type(key,(),{'__pyunostruct__':key,'__setattr__':original})
    if problem=='foreign_setter':cls.__setattr__=lambda *a:None
    before=[q.__dict__['__setattr__'] for q in u.classes.values()]
    raises(ValueError,lambda:c.install_request_args_compat(u));ok('preflight_refuses_'+problem,before==[q.__dict__['__setattr__'] for q in u.classes.values()])
    cls.__pyunostruct__=key;cls.__setattr__=original
# Genuine delegate errors retain identity and args, no swallowing/classification.
u=U();delegated=RuntimeError(SECRET)
def fail(self,name,value):raise delegated
u._uno_struct__setattr__=fail
for cls in u.classes.values():cls.__setattr__=fail
t=c.install_request_args_compat(u)
try:
    x,f=obj(u);ok('original_delegate_exception_identity_preserved',raises(RuntimeError,lambda:setattr(x,'Message',SECRET)) is delegated)
finally:
    c.restore_request_args_compat(t)
    for cls in u.classes.values():cls.__setattr__=original
# Whole-token CAS refuses before overwriting foreign mutation. Client MUST exit; test restores only its synthetic fixture.
u=U();t=c.install_request_args_compat(u);foreign=lambda *a:None;t[-1][0].__setattr__=foreign
raises(ValueError,lambda:c.restore_request_args_compat(t));ok('restore_CAS_refuses_foreign_mutation_no_overwrite',t[-1][0].__dict__['__setattr__'] is foreign and all(row[0].__dict__['__setattr__'] is row[2] for row in t[:-1]))
t[-1][0].__setattr__=t[-1][2];c.restore_request_args_compat(t)
# No secrets in any output/log on exact sixth args or delegated error paths.
buf=io.StringIO()
with contextlib.redirect_stdout(buf),contextlib.redirect_stderr(buf):
    u=U();t=c.install_request_args_compat(u)
    try:x,f=obj(u);x.args=(SECRET,);raises(TypeError,lambda:setattr(x,'ErrCode',SECRET))
    finally:c.restore_request_args_compat(t)
ok('no_stdout_stderr_values_or_credentials',buf.getvalue()=='')
# Integration with exact old once-only probe and metadata observer, now matching six-token arity.
# Deliberate validation-negative fixtures left no foreign setters anywhere.
gc.collect();u=U();t=c.install_request_args_compat(u);x,f=obj(u)
class Request:
    def __init__(self,error=None):self.calls=0;self.error=error
    def getRequest(self):
        self.calls+=1
        if self.error is not None:raise self.error
        x.args=(SECRET,);return x
    def getContinuations(self):return []
try:
    p=probe_mod.OneShotConversionProbe(u,t);r=Request();event={};value=p.get_request(r,event)
    ok('six_token_probe_one_call_returns_real_same_object',value is x and r.calls==1 and event['get_request_calls']==1 and event['restored'] and not event['cleanup_failures'])
    raises(probe_mod.ProbeRefused,lambda:p.get_request(r,{}));ok('second_getRequest_refused_before_call',r.calls==1)
    other=RuntimeError(SECRET);p=probe_mod.OneShotConversionProbe(u,t);r=Request(other);event={};got=raises(RuntimeError,lambda:p.get_request(r,event))
    ok('getRequest_failure_reraised_unchanged_and_restored',got is other and r.calls==1 and event['restored'] and u._uno_struct__setattr__ is original)
    # Reentry consumes no second getRequest; outer error restored and propagated.
    p=probe_mod.OneShotConversionProbe(u,t)
    class Reentrant:
        calls=0
        def getRequest(self):self.calls+=1;return p.get_request(self,{})
    r=Reentrant();event={};raises(probe_mod.ProbeRefused,lambda:p.get_request(r,event));ok('reentry_refused_and_restored',r.calls==1 and event['restored'])
    # Exact unchanged observer will still classify base ErrorCodeRequest OTHER; no ErrCode reads/acceptance expansion.
    class UH:Base=type('Base',(),{})
    class IH:pass
    p=probe_mod.OneShotConversionProbe(u,t);handler=cb.make_abort_handler(u,UH,IH,u.classes[c.REQUEST_NAMES[0]],u.classes[c.REQUEST_NAMES[1]],u.classes[c.REQUEST_NAMES[4]],request_probe=p)
    r=Request();handler.handle(r);ev=handler.events[0]
    ok('base_ErrorCodeRequest_is_not_password_or_benign_acceptance',ev['request_kind']=='OTHER' and ev['payload_class']=='com.sun.star.task.ErrorCodeRequest' and 'error_code' not in ev and not cb.observed_password_abort(handler.events) and not cb.observed_password_refusal_sequence(handler.events,'odt'))
    # Pure extract ONLY real protocol validation functions/constants; no side-effectful client import.
    tree=ast.parse(source['diagnostic_client.py']);wanted={'QUALIFIED','PHASES','KNOWN_PAYLOADS','REASONS'}
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('need','class_identity','exception_projection','probe_projection','adapter_projection','terminal_reasons') or isinstance(n,ast.Assign) and any(isinstance(a,ast.Name) and a.id in wanted for a in n.targets)]
    import re
    cli={'re':re};exec(compile(ast.Module(body=nodes,type_ignores=[]),'protocol_ast_only','exec'),cli)
    d={'schema':'friday.f06.one-bridge-observation.v1','state':'DIAGNOSTIC_NOT_QUALIFICATION','load_calls':1,'opened':True,'semantic_match':True,'close_attempted':True,'closed_or_disposed':True,'planned_stores':0,'store_count_instrumented':False,'original_strict_all_pass':False,'acceptance_granted':False,'actual_payload_type':'UNKNOWN','interaction_events':handler.events,'get_request_window_consumed':True}
    cli['adapter_projection'](d);ok('unchanged_nearest_protocol_keeps_UNKNOWN_not_PASS',cli['terminal_reasons'](d)==['UNKNOWN_CLASS_IDENTITY'])
    ok('original_class1_raw_stays_terminal_strict_false',actual['state']=='TERMINAL_STOP' and actual['original_strict_all_pass'] is False)
finally:c.restore_request_args_compat(t)
ok('final_global_and_class_custody_restored',u._uno_struct__setattr__ is original and all(cls.__dict__['__setattr__'] is original for cls in u.classes.values()))
ok('no_UNO_or_application_modules_loaded',not any(n in sys.modules for n in ('uno','pyuno','run_agent','unohelper')))
print(json.dumps({'schema':'task27.pure-controls.v1','scope':'SYNTHETIC_PYTHON_ONLY_NOT_PYUNO_APP','checks':checks,'count':len(checks),'all_pass':True,'failure_reproduction':'real uno.py setter AST with synthetic generated class/backing; outer C pending-error/SystemError is observed historical evidence, not recreated native bridge','strict_old_and_new_raw_verdicts_unchanged':True},sort_keys=True))
