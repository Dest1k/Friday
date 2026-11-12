"""Affected final helper->probe->observer->adapter->client protocol, synthetic only."""
import ast,types,pathlib,sys,json,re
B=pathlib.Path(__file__).resolve().parent;R=B/'revision2/candidate';mods={}
for name in ('request_args_compat_v2','conversion_probe','callback_observer_v2','readonly_diagnostic'):
 m=types.ModuleType(name);exec(compile((R/(name+'.py')).read_text(),name+'.py','exec'),m.__dict__);sys.modules[name]=m;mods[name]=m
h=mods['request_args_compat_v2'];obs=mods['readonly_diagnostic'];tree=ast.parse((B/'baseline/uno.py').read_text());node=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='_uno_struct__setattr__');ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'uno.py','exec'),ns);setter=ns[node.name]
checks=[]
def ok(n,v):assert v,n;checks.append({'name':n,'pass':True})
class Backing:__slots__=()
def init(self,value):self.__dict__['value']=value
class U:
 _uno_struct__setattr__=staticmethod(setter)
 def __init__(self):
  self.cs={n:type(n,(Exception,),{'__pyunostruct__':n,'__init__':init,'__setattr__':setter})for n in h.REQUEST_NAMES}
  self.cs[h.REQUEST_NAMES[4]]=type(h.REQUEST_NAMES[4],(self.cs[h.REQUEST_NAMES[5]],),{'__pyunostruct__':h.REQUEST_NAMES[4],'__init__':init,'__setattr__':setter})
 def getClass(self,n):return self.cs[n]
class UH:Base=type('Base',(),{})
class IH:pass
class PV:pass
class Doc:
 closed=0
 def close(self,flag):self.closed+=1
class Request:
 def __init__(self,u,raises_error=False):self.u=u;self.calls=0;self.raises_error=raises_error
 def getRequest(self):
  self.calls+=1;val=self.u.cs[h.REQUEST_NAMES[-1]](Backing());val.args=('SYNTHETIC_VALUE',)
  if self.raises_error:raise val
  return val
 def getContinuations(self):return []
class Desktop:
 def __init__(self,u,error=False):self.calls=0;self.doc=Doc();self.request=Request(u,error);self.props=None
 def loadComponentFromURL(self,url,target,flags,props):
  self.calls+=1;self.props={p.Name:p.Value for p in props};self.props['InteractionHandler'].handle(self.request);return self.doc
# Exact unchanged client projection/terminal policy extracted without importing effectful client.
tree=ast.parse((R/'diagnostic_client.py').read_text());constants={'QUALIFIED','PHASES','KNOWN_PAYLOADS','REASONS'};fn={'need','class_identity','exception_projection','probe_projection','adapter_projection','terminal_reasons'}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in fn or isinstance(n,ast.Assign)and any(isinstance(a,ast.Name)and a.id in constants for a in n.targets)];cli={'re':re};exec(compile(ast.Module(body=nodes,type_ignores=[]),'client_protocol_only','exec'),cli)
for raised in (False,True):
 u=U();desktop=Desktop(u,raised);token=h.install_request_args_compat(u)
 try:
  result=obs.observe_one_readonly(uno=u,unohelper=UH,desktop=desktop,property_value=PV,interaction_handler_type=IH,password_request_type=u.cs[h.REQUEST_NAMES[0]],ms_password_request_type=u.cs[h.REQUEST_NAMES[1]],error_code_request_type=u.cs[h.REQUEST_NAMES[4]],compat_token=token,selected_file_url='file:///inputs/native-outputs/retained-source.ott',correct_password='SYNTHETIC_ONLY',semantic_check=lambda d:True)
  cli['adapter_projection'](result);reasons=cli['terminal_reasons'](result)
  label='raised'if raised else'returned'
  ok(label+'_one_load_one_getrequest',desktop.calls==1 and desktop.request.calls==1 and result['load_calls']==1)
  ok(label+'_strict_false_no_acceptance',result['original_strict_all_pass']is False and result['acceptance_granted']is False and result['planned_stores']==0)
  ok(label+'_hook_cleanup',all(e['conversion_probe']['restored']and not e['conversion_probe']['cleanup_failures']for e in result['interaction_events']))
  if not raised:
   ok('returned_base_ErrorCodeRequest_metadata_not_accepted',result['opened']and result['semantic_match']and result['closed_or_disposed']and reasons==['UNKNOWN_CLASS_IDENTITY']and result['interaction_events'][0]['request_kind']=='OTHER'and 'error_code'not in result['interaction_events'][0])
  else:
   ok('raised_ErrorCodeRequest_stays_callback_load_fault',not result['opened']and 'CALLBACK_FAULT'in reasons and 'LOAD_OR_SEMANTIC_FAULT'in reasons and result['interaction_events'][0]['callback_error']['exception_class']=='com.sun.star.task.ErrorCodeRequest')
  props=desktop.props
  ok(label+'_original_readonly_properties_unchanged',all(props[k]is v for k,v in (('Hidden',True),('ReadOnly',True),('AsTemplate',False)))and props['MacroExecutionMode']==0 and props['UpdateDocMode']==0)
 finally:h.restore_request_args_compat(token)
 ok(label+'_six_restored',all(c.__dict__['__setattr__']is setter for c in u.cs.values())and u._uno_struct__setattr__ is setter)
encoded=json.dumps({'checks':checks,'count':len(checks),'all_pass':True,'scope':'SYNTHETIC_FINAL_SOURCE_PROTOCOL_NOT_OFFICE','old_runtime_verdict_unchanged':True},sort_keys=True);assert 'SYNTHETIC_VALUE'not in encoded and 'SYNTHETIC_ONLY'not in encoded;print(encoded)
