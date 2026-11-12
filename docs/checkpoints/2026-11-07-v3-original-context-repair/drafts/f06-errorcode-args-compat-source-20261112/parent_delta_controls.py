"""Independent parent check of reviewer exact-str/custody delta, synthetic only."""
import ast,json,pathlib,sys,types,contextlib,io
B=pathlib.Path(__file__).resolve().parent;R=B/'revision2';p=R/'candidate/request_args_compat_v2.py';src=p.read_text();m=types.ModuleType('reviewed_compat');exec(compile(src,str(p),'exec'),m.__dict__)
checks=[]
def ok(n,v):assert v,n;checks.append({'name':n,'pass':True})
def failure(cls,fn):
 try:fn()
 except cls as e:return e
 raise AssertionError('EXPECTED_EXCEPTION')
class Fields:
 def __init__(self):object.__setattr__(self,'seen',[])
 def __setattr__(self,name,value):
  self.seen.append((name,value))
  if type(name)is not str:raise TypeError('ORIGINAL_NAME')
  if name=='args':raise AttributeError('ORIGINAL_ARGS')
  if name not in ('Message','Context','ErrCode'):raise AttributeError('ORIGINAL_UNKNOWN')
  object.__setattr__(self,name,value)
def original(self,name,value):return setattr(self.__dict__['value'],name,value)
def init(self,value):self.__dict__['value']=value
class U:
 def __init__(self):
  self._uno_struct__setattr__=original
  self.classes={name:type(name,(Exception,),{'__pyunostruct__':name,'__setattr__':original,'__init__':init}) for name in m.REQUEST_NAMES}
 def getClass(self,name):return self.classes[name]
def x(u):f=Fields();return u.classes[m.REQUEST_NAMES[-1]](f),f
class Name(str):
 def __eq__(self,other):return other=='args'
 __hash__=str.__hash__
class Marker(str):
 def __eq__(self,other):return True
 __hash__=str.__hash__
# No document/password/native modules are available or used.
u=U();t=m.install_request_args_compat(u)
try:
 a,f=x(u);a.args=('SYNTHETIC_HIDDEN',);ok('exact_args_descriptor_no_UNO_delegate',a.args==('SYNTHETIC_HIDDEN',) and not f.seen)
 e=failure(TypeError,lambda:a.__setattr__(Name('ErrCode'),(19,)))
 ok('str_subclass_comparison_trap_delegates_original',str(e)=='ORIGINAL_NAME' and type(f.seen[-1][0]) is Name)
 class Eq:
  def __eq__(self,other):return True
 before=list(f.seen);e=failure(TypeError,lambda:a.__setattr__(Eq(),(19,)))
 ok('nonstring_comparison_trap_delegates_original',type(e)is TypeError and f.seen==before)
 a.ErrCode=525;ok('original_nonargs_value_untouched',f.ErrCode==525)
except BaseException:raise
finally:m.restore_request_args_compat(t)
ok('six_normal_restore',all(c.__dict__['__setattr__']is original for c in u.classes.values()))
u=U();u.classes[m.REQUEST_NAMES[-1]].__pyunostruct__=Marker(m.REQUEST_NAMES[-1]);failure(ValueError,lambda:m.install_request_args_compat(u));ok('marker_str_subclass_refused_before_writes',all(c.__dict__['__setattr__']is original for c in u.classes.values()))
# Determine original helper installation loop from stable code, no source-body patching.
install=m.install_request_args_compat;lines=src.splitlines();loop=next(i for i,line in enumerate(lines,1)if 'for name, (cls, old_setter, replacement) in zip(REQUEST_NAMES, token):'in line)
for kind in ('later_class','already_patched','keyboard_interrupt','helper','factory','marker'):
 u=U();cs=list(u.classes.values());foreign=lambda *a:None;primary=KeyboardInterrupt('SYNTHETIC_HIDDEN') if kind=='keyboard_interrupt' else RuntimeError('SYNTHETIC_HIDDEN')
 state={'loops':0,'injected':False};factory_original=u.getClass
 def trace(frame,event,arg):
  if frame.f_code is install.__code__ and event=='line'and frame.f_lineno==loop:
   state['loops']+=1
   if state['loops']==2:
    state['injected']=True
    if kind=='later_class':cs[-1].__setattr__=foreign
    elif kind=='already_patched':cs[0].__setattr__=foreign;raise primary
    elif kind=='keyboard_interrupt':raise primary
    elif kind=='helper':u._uno_struct__setattr__=foreign
    elif kind=='factory':u.getClass=lambda name:None
    elif kind=='marker':cs[-1].__pyunostruct__='com.sun.star.task.Foreign'
  return trace
 err=None
 try:
  sys.settrace(trace)
  try:m.install_request_args_compat(u)
  except BaseException as e:err=e
 finally:sys.settrace(None)
 ok('injected_'+kind,state['injected']and err is not None)
 if kind in ('already_patched','keyboard_interrupt'):ok('primary_identity_'+kind,err is primary)
 if kind=='later_class':ok('later_foreign_preserved_own_rollback',cs[-1].__dict__['__setattr__']is foreign and all(c.__dict__['__setattr__']is original for c in cs[:-1]))
 elif kind=='already_patched':ok('earlier_foreign_preserved',cs[0].__dict__['__setattr__']is foreign and all(c.__dict__['__setattr__']is original for c in cs[1:]))
 else:ok('owned_only_rollback_'+kind,all(c.__dict__['__setattr__']is original for c in cs))
 # Dispose fixture; no production restore is claimed for foreign mutation.
u=U();t=m.install_request_args_compat(u);foreign=lambda *a:None;t[-1][0].__setattr__=foreign
failure(ValueError,lambda:m.restore_request_args_compat(t));ok('final_restore_foreign_CAS_still_no_partial_overwrite',t[-1][0].__dict__['__setattr__']is foreign and all(c.__dict__['__setattr__']is replacement for c,_,replacement in t[:-1]))
# Source-level private guarded code has no logging/I/O/exception value introspection.
tr=ast.parse(src);ok('no_logging_or_value_serialization_calls',not any(isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id in ('print','repr','str','open','eval','exec')for n in ast.walk(tr)))
ok('no_UNO_or_application_imported',not any(n in sys.modules for n in ('uno','pyuno','unohelper','run_agent')))
print(json.dumps({'schema':'task27.parent-reviewer-delta.v1','scope':'SYNTHETIC_PYTHON_ONLY','checks':checks,'count':len(checks),'all_pass':True,'revision':'revision2','r1_controls_reused_only_unchanged_scope':True},sort_keys=True))
