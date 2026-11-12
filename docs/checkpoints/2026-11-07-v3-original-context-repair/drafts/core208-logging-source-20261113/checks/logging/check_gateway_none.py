import ast, copy, hashlib, json, logging, os
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime
from zoneinfo import ZoneInfo
P=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F06-INBOUND-PREVIEW-SOURCE-20261112')
R=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F06-INBOUND-PREVIEW-CANDIDATE-REVIEW-20261112')
class Capture:
 def __init__(self): self.records=[]
 def info(self,fmt,*args):
  record=logging.LogRecord('bounded.source',logging.INFO,'synthetic',1,fmt,args,None)
  self.records.append(record.getMessage())
checks=[]
for side in ['preimage','source']:
 source=P/side/'gateway/run_turn.py'
 tree=ast.parse(source.read_text())
 function=next(n for n in ast.walk(tree) if isinstance(n,ast.AsyncFunctionDef) and n.name=='_handle_message_with_agent')
 platform=next(n for n in function.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_platform_name' for t in n.targets))
 log=next(n for n in function.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='logger.info')
 code=compile(ast.fix_missing_locations(ast.Module(body=[platform,log],type_ignores=[])),str(source),'exec')
 event=SimpleNamespace(text=None,reply_to_text=None,reply_to_message_id=None,media_urls=None,message_type=SimpleNamespace(value='text'))
 origin=SimpleNamespace(platform=SimpleNamespace(value='synthetic'),user_name='synthetic-user',user_id='synthetic-id',chat_id='synthetic-chat')
 before=copy.deepcopy(event.__dict__)
 capture=Capture()
 exec(code,{'event':event,'source':origin,'logger':capture})
 assert len(capture.records)==1 and event.__dict__==before
 line=capture.records[0]
 if side=='source':
  assert 'kind=text attachments=0 msg_chars=0 reply_to_id=None reply_to_chars=0' in line
  assert 'msg=' not in line and 'reply_to_text=' not in line
 else:
  assert "msg='' reply_to_id=None reply_to_text=''" in line
 checks.append({'check':side+' exact gateway production AST supports None text/reply/media with standard logging interpolation and input preservation','passed':True,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'line_start':platform.lineno,'line_end':log.end_lineno})
result={'state':'PASS_TWO_NEW_BOUNDED_GATEWAY_NONE_CONTROLS','completed_moscow':datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),'reason':'Independent harness review identified gateway None as statically safe but not explicitly executed in prior 61; test only this missing input with exact source statements and standard logging.LogRecord formatting. Prior 61 unchanged checks not rerun.','checks':checks,'scope':'Isolated exact source AST containing platform assignment and INFO statement; synthetic in-memory data only, no product imports/startup/resources.'}
out=R/'BOUNDED-NONE-CHECKS.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');os.chmod(out,0o600)
print(json.dumps({'state':result['state'],'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
