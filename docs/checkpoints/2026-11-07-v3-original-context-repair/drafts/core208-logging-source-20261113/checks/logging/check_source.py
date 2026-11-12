"""Bounded source-extracted checks. No native imports, product IO or user data."""
from __future__ import annotations
import ast
import asyncio
import copy
import difflib
import enum
import hashlib
import json
import logging
from pathlib import Path
from types import SimpleNamespace as NS
import time

P = Path(__file__).resolve().parents[1]
N = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent')
RESULTS = []

def check(name, condition):
    assert condition, name
    RESULTS.append({'check': name, 'passed': True})

def tree(rel, candidate=True):
    return ast.parse((P/('source' if candidate else 'preimage')/rel).read_text())

def function(t, name):
    return copy.deepcopy(next(n for n in ast.walk(t) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name == name))

def execute(nodes, namespace):
    module = ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*copy.deepcopy(nodes)],type_ignores=[])
    exec(compile(ast.fix_missing_locations(module),'<source-extracted bounded check>','exec'),namespace)

class Capture(logging.Handler):
    def __init__(self):
        super().__init__(); self.records=[]
    def emit(self, record): self.records.append(record)
    def clear(self): self.records.clear()
    def rendered(self): return '\n'.join(record.getMessage() for record in self.records)

logger=logging.Logger('bounded.own',logging.INFO); capture=Capture(); logger.addHandler(capture)
# Actual native enum declaration, no package import.
event_tree=ast.parse((N/'gateway/platforms/event.py').read_text())
env={'Enum':enum.Enum}; execute([next(n for n in event_tree.body if isinstance(n,ast.ClassDef) and n.name=='MessageType')],env)
MessageType=env['MessageType']

# Full candidate/original functions compile. The unchanged execution body is
# compared after the sole modified diagnostic span is removed.
for rel, fname, start, end in [
 ('gateway/run_turn.py','_handle_message_with_agent','logger.info','resolved'),
 ('agent/turn_context.py','build_turn_context','_preview_text','messages')]:
    before=tree(rel,False); after=tree(rel,True)
    compile(before,str(P/'preimage'/rel),'exec'); compile(after,str(P/'source'/rel),'exec')
    def normalized(t):
        f=function(t,fname)
        if rel.startswith('gateway/'):
            f.body=[n for n in f.body if not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=='logger' and n.value.func.attr=='info' and n.value.args and isinstance(n.value.args[0],ast.Constant) and n.value.args[0].value.startswith('inbound message:'))]
        else:
            a=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='_preview_text' for x in n.targets))
            b=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='messages' for x in n.targets))
            del f.body[a:b]
        return ast.dump(f,include_attributes=False)
    check(rel+' full compile and unchanged execution outside diagnostic', normalized(before)==normalized(after))

# Actual gateway coroutine runs through its first diagnostic to the resolver.
# It returns there, with no session, model or delivery resources created.
class Runner:
    async def _hmwa_resolve_session(self,event,source):
        self.event=event; self.source=source
        return None

source=NS(platform=NS(value='telegram'),user_name='synthetic-user',user_id='synthetic-id',chat_id='synthetic-chat')
gateway_cases=[
 ('document-caption', 'CAPTION_SENTINEL_37 short', MessageType.DOCUMENT,['/synthetic.bin'],'REPLY_SENTINEL_42'),
 ('same-upload-continuation','CONTINUATION_SENTINEL_54 '+('x'*140),MessageType.TEXT,[],''),
 ('multiline-unicode','UNICODE_SENTINEL_62\nЖ🙂',MessageType.TEXT,[],None),
 ('empty-caption','',MessageType.DOCUMENT,['/synthetic.bin'],''),
 ('reply-only','',MessageType.TEXT,[],'REPLY_SENTINEL_73 '+('y'*120)),
 ('voice-caption','VOICE_SENTINEL_81',MessageType.VOICE,['/synthetic.ogg'],None),
]
for name,text,kind,media,reply in gateway_cases:
    event=NS(text=text,message_type=kind,media_urls=media,reply_to_message_id='synthetic-reply' if reply else None,reply_to_text=reply)
    snapshot=copy.deepcopy(event.__dict__)
    for candidate in (False,True):
        capture.clear(); ns={'logger':logger,'time':time}; execute([function(tree('gateway/run_turn.py',candidate),'_handle_message_with_agent')],ns)
        runner=Runner(); asyncio.run(ns['_handle_message_with_agent'](runner,event,source,'synthetic-session',1))
        rendered=capture.rendered()
        leaks=any(token in rendered for token in ['CAPTION_SENTINEL','CONTINUATION_SENTINEL','UNICODE_SENTINEL','REPLY_SENTINEL','VOICE_SENTINEL'])
        if candidate:
            check('gateway '+name+' metadata only',not leaks and 'platform=telegram' in rendered and 'synthetic-user' in rendered and f'kind={kind.value}' in rendered and f'attachments={len(media)}' in rendered and f'msg_chars={len(text)}' in rendered and f'reply_to_chars={len(reply or "")}' in rendered)
            check('gateway '+name+' original input unchanged',runner.event is event and event.__dict__==snapshot)
        elif text or reply:
            check('negative control old gateway '+name+' raw preview detected',leaks)

# Execute the exact log-prologue AST span, preserving its origin branch.
# The real summarizer implementation/dependencies are extracted unchanged.
summary_tree=ast.parse((N/'agent/codex_responses_adapter.py').read_text())
summary_names=['_str_or_empty','_part_type','_nonempty_str','_as_list','_iter_content_parts','_summarize_user_message_for_log']
summary_env={'_TEXT_PART_TYPES':{'text','input_text','output_text'},'_IMAGE_PART_TYPES':{'image_url','input_image'}}
execute([function(summary_tree,name) for name in summary_names],summary_env)
summarize=summary_env['_summarize_user_message_for_log']
metadata_tree=ast.parse((N/'agent/message_metadata.py').read_text())
stage_env={'wall_time':lambda:123.0}; execute([function(metadata_tree,'stamp_message_timestamp'),function(metadata_tree,'append_message'),function(tree('agent/turn_context.py'),'_stage_turn_user_message')],stage_env)
agent_cases=[
 ('short-string','TEXT_SENTINEL_10'),('long-continuation','CONTINUE_SENTINEL_11 '+('z'*160)),
 ('unicode','UNICODE_SENTINEL_12\nЖ🙂'),('empty',''),('none',None),
 ('multimodal',[{'type':'text','text':'MULTIMODAL_SENTINEL_13'},{'type':'image_url','image_url':{'url':'synthetic:IMAGE_URL_SENTINEL_14'}}]),
 ('responses-parts',[{'type':'input_text','text':'INPUT_SENTINEL_15'},{'type':'input_image','image_url':'synthetic:IMAGE_URL_SENTINEL_16'}]),
 ('scalar-dict',{'text':'SCALAR_SENTINEL_17'}),
]
for name,value in agent_cases:
    snapshot=copy.deepcopy(value)
    history=[{'role':'user','content':'OLD_HISTORY_SENTINEL_18'}]; history_snapshot=copy.deepcopy(history)
    for candidate in (False,True):
        f=function(tree('agent/turn_context.py',candidate),'build_turn_context')
        a=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='_preview_text' for x in n.targets))
        b=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='messages' for x in n.targets))
        capture.clear(); agent=NS(session_id='synthetic-session',model='synthetic-model',provider='synthetic-provider',platform='telegram',_turn_origin='synthetic-origin')
        ns={'agent':agent,'user_message':value,'conversation_history':history,'logger':logger,'summarize_user_message_for_log':summarize}
        execute(f.body[a:b],ns); rendered=capture.rendered()
        if candidate:
            check('agent '+name+' metadata only', 'SENTINEL' not in rendered and 'synthetic-session' in rendered and 'synthetic-model' in rendered and 'synthetic-provider' in rendered and 'platform=telegram' in rendered and 'history=1' in rendered and f'input_type={type(value).__name__}' in rendered and f'content_parts={ {"none":0,"multimodal":2,"responses-parts":2}.get(name,1)}' in rendered and f'msg_chars={len(summarize(value))}' in rendered and 'origin=synthetic-origin' in rendered)
            check('agent '+name+' exact input/history unchanged',value==snapshot and history==history_snapshot)
            # The existing nonquiet user-facing preview still has its input.
            check('agent '+name+' print preview variable preserved', ns['_preview_text']==summarize(value))
            display={'synthetic':'retained'}
            user,_=stage_env['_stage_turn_user_message'](agent,value,None,123.0,'synthetic-message',None,display)
            messages=list(history); stage_env['append_message'](messages,user,timestamp=123.0)
            check('agent '+name+' actual user staging/append preserves content',user['content'] is value and user['role']=='user' and user['display_metadata'] is display and user['platform_message_id']=='synthetic-message' and messages[-1] is user and history==history_snapshot)
        elif name not in {'none','empty'}:
            check('negative control old agent '+name+' raw preview detected', 'SENTINEL' in rendered)

# Source pins must remain the exact installed preimages: no runtime source write.
pins=json.loads((P/'SOURCE-PINS.json').read_text())
for row in pins['files']:
    check(row['relative_path']+' installed preimage retained',hashlib.sha256(Path(row['installed_path']).read_bytes()).hexdigest()==row['preimage_sha256'])
    check(row['relative_path']+' candidate byte identity',hashlib.sha256(Path(row['candidate_path']).read_bytes()).hexdigest()==row['candidate_sha256'])
output={'state':'PASS_BOUNDED_SOURCE_EXTRACTED_NOT_RUNTIME','count':len(RESULTS),'checks':RESULTS,'limits':['Only actual source-extracted logsites plus unmodified summarizer/staging/append consumers executed with synthetic inputs.','No native package imports, model, file/Office/Telegram operation, product history/DB/log access, runtime install or actual user replay.','Full dispatcher/build_turn_context execution is not claimed.']}
(P/'boundedchecks/RESULT.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({'state':output['state'],'checks':len(RESULTS)}))
