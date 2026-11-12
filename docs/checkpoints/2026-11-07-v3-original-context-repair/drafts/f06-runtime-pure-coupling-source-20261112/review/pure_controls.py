import os, sys, resource, signal, json, copy, logging, importlib.util, hashlib
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(60,60))
resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024))
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024*1024,4*1024*1024))
signal.alarm(90)
os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]))
review=Path(__file__).resolve().parent
stand=review/'stand'
sys.path.insert(0,str(stand))
blocked=[]
def audit(event,args):
    if event.startswith(('socket.','subprocess.','os.system','os.fork','os.exec')):
        blocked.append(event)
        raise AssertionError('forbidden effect')
sys.addaudithook(audit)
assert not (stand/'run_agent.py').exists()
assert not (stand/'agent/context_compressor.py').exists()
assert not (stand/'hermes_cli').exists()
from agent import message_sanitization as s
from agent import message_metadata as m
from agent import tool_dispatch_helpers as t
assert s._DB_PERSISTED_MARKER is m._DB_PERSISTED_MARKER
assert importlib.util.find_spec('run_agent') is None
assert importlib.util.find_spec('agent.context_compressor') is None
assert importlib.util.find_spec('hermes_cli') is None
assert importlib.util.find_spec('agent.vision_message_prep') is None
initial_closure=sorted(k for k in sys.modules if k=='agent' or k.startswith(('agent.','tools.')) or k=='tools')
assert not any(k=='run_agent' or k.startswith('hermes_cli') or k=='agent.context_compressor' or k=='agent.vision_message_prep' for k in sys.modules)
class Capture(logging.Handler):
    def __init__(self):
        super().__init__(); self.records=[]
    def emit(self,record):self.records.append(record)
h=Capture(); log=logging.getLogger('review.pure'); log.handlers=[h]; log.propagate=False; log.setLevel(logging.WARNING)
checks=[]
def check(name, condition):
    assert condition,name
    checks.append(name)
def tc(raw, *, id='old_id', call_id=None, name='read_file', response_item_id=None):
    v={'id':id,'type':'function','function':{'name':name,'arguments':raw}}
    if call_id is not None:v['call_id']=call_id
    if response_item_id is not None:v['response_item_id']=response_item_id
    return v
def am(call):return {'role':'assistant','content':None,'tool_calls':[call],m._DB_PERSISTED_MARKER:True}
def apply(msgs,**kw):return s.sanitize_tool_call_arguments(msgs,logger=log,session_id='synthetic-review',**kw)
# Real leaf import is the positive boundary; unavailable dependencies stay absent.
check('actual_leaf_import_without_app_compressor_config_vision', True)
for value in (None,(),{},'bad'):
    check('nonlist_noop_'+type(value).__name__,apply(value)==0)
valid=[am(tc('{"path":"example.txt"}')),{'role':'user','content':'kept'}]
before=copy.deepcopy(valid); ids=list(map(id,valid)); n=len(h.records)
check('valid_json_no_mutation',apply(valid)==0 and valid==before and list(map(id,valid))==ids and len(h.records)==n)
for raw in (None,'','  \n '):
    msgs=[am(tc(raw))]; n=len(h.records)
    check('empty_coerces_without_warn_or_stub_'+repr(raw),apply(msgs)==0 and len(msgs)==1 and msgs[0]['tool_calls'][0]['function']['arguments']=='{}' and m._DB_PERSISTED_MARKER not in msgs[0] and len(h.records)==n)
for raw in ({'path':'x'},[],3,False):
    msgs=[am(tc(raw))]; before=copy.deepcopy(msgs); n=len(h.records)
    check('nonstring_arguments_noop_'+type(raw).__name__,apply(msgs)==0 and msgs==before and len(h.records)==n)
# malformed credential-bearing inputs never appear in captured diagnostic rendering.
for raw,name in [('{"password":"SYNTHETIC-CREDENTIAL-NEVER-REAL",','read_file'),('{"format":"odf_password_edit","content":{"password":"SYNTHETIC-CREDENTIAL-NEVER-REAL"},','write_file')]:
    msgs=[am(tc(raw,name=name))]; n=len(h.records)
    result=apply(msgs)
    check('protected_malformed_warning_redacts_'+name,result==1 and len(h.records)==n+1 and 'SYNTHETIC-CREDENTIAL-NEVER-REAL' not in h.records[-1].getMessage() and 'redacted' in h.records[-1].getMessage())
    check('stub_real_constructor_'+name,msgs[1]['role']=='tool' and msgs[1]['name']==name and msgs[1]['tool_name']==name and msgs[1]['tool_call_id']=='old_id' and msgs[1]['content']==s._TOOL_CALL_ARGUMENTS_CORRUPTION_MARKER and isinstance(msgs[1].get('timestamp'),(int,float)))
# Both call-id field forms and bridge result aliases use the actual shared policy.
for result_id in ('canon','resp','canon|resp'):
    call=tc('{',id='fallback',call_id=' canon|resp ',response_item_id='resp')
    result={'role':'tool','tool_call_id':result_id,'content':{'ok':False},m._DB_PERSISTED_MARKER:True}
    msgs=[am(call),result]; n=len(h.records)
    check('existing_alias_result_'+result_id,apply(msgs)==1 and len(msgs)==2 and msgs[1] is result and result['content']==s._TOOL_CALL_ARGUMENTS_CORRUPTION_MARKER+'\n'+json.dumps({'ok':False}) and m._DB_PERSISTED_MARKER not in result and m._DB_PERSISTED_MARKER not in msgs[0] and h.records[n].args[2]=='canon')
# Duplicate identifiers preserve old shared-result behavior rather than adding an orphan stub.
msgs=[{'role':'assistant','tool_calls':[tc('{'),tc('[',name='write_file')]}]
check('duplicate_id_one_stub_two_repairs',apply(msgs)==2 and len(msgs)==2 and msgs[1]['tool_call_id']=='old_id' and msgs[1]['content']==s._TOOL_CALL_ARGUMENTS_CORRUPTION_MARKER)
# A non-tool boundary stops matching; a later same-id result is not mutated.
later={'role':'tool','tool_call_id':'old_id','content':'untouched'}
msgs=[am(tc('{')),{'role':'user','content':'boundary'},later]
check('noncontiguous_result_not_matched',apply(msgs)==1 and len(msgs)==4 and msgs[3] is later and later['content']=='untouched')
# Cursor identity is retained and skips unchanged messages, then notices replacement/appends.
msgs=[am(tc('{'))]; cursor={}; apply(msgs,cursor=cursor); n=len(h.records)
check('cursor_strong_reference_prefix',all(a is b for a,b in zip(cursor['prefix'],msgs)))
check('cursor_repeat_noop',apply(msgs,cursor=cursor)==0 and len(h.records)==n)
msgs.append(am(tc('{',id='new')))
check('cursor_appended_scanned',apply(msgs,cursor=cursor)==1 and len(msgs)==4 and msgs[-1]['tool_call_id']=='new')
msgs[0]=am(tc('{',id='replacement'))
check('cursor_replacement_rescanned',apply(msgs,cursor=cursor)==1 and msgs[1]['tool_call_id']=='replacement')
# Default warning logger preserves the old runtime helper channel.
oldlog=logging.getLogger('agent.agent_runtime_helpers');oldlog.handlers=[h];oldlog.propagate=False;oldlog.setLevel(logging.WARNING)
msgs=[am(tc('{',name='ordinary_tool'))]; n=len(h.records);s.sanitize_tool_call_arguments(msgs)
check('default_logger_name_preserved',len(h.records)==n+1 and h.records[-1].name=='agent.agent_runtime_helpers')
# Untrusted result construction still routes through the actual constructor and wrappers.
msgs=[am(tc('{',name='web_search'))];apply(msgs)
check('untrusted_stub_constructed_by_existing_policy','<untrusted_tool_result' in msgs[1]['content'] and s._TOOL_CALL_ARGUMENTS_CORRUPTION_MARKER in msgs[1]['content'])
check('no_effect_attempts',not blocked)
check('final_no_app_compressor_config_vision_imports',not any(k=='run_agent' or k.startswith('hermes_cli') or k=='agent.context_compressor' or k=='agent.vision_message_prep' for k in sys.modules))
print(json.dumps({'status':'PASS','checks':checks,'check_count':len(checks),'actual_import_closure':initial_closure,'effect_attempts':blocked,'affinity_cpus':len(os.sched_getaffinity(0)),'jiter_best_effort_preloaded':sys.modules['agent.jiter_preload']._JITER_PRELOADED,'scope':'actual candidate leaf import and synthetic in-memory semantics only; no runtimehelper/app admission claim'},sort_keys=True))
