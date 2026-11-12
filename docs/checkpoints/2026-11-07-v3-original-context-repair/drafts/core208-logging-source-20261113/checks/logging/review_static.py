from pathlib import Path
import ast, difflib, hashlib, json, os
from datetime import datetime
from zoneinfo import ZoneInfo
P=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F06-INBOUND-PREVIEW-SOURCE-20261112')
R=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F06-INBOUND-PREVIEW-CANDIDATE-REVIEW-20261112')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def record(p):
 s=p.stat(); return {'path':str(p),'bytes':s.st_size,'sha256':sha(p),'mode':oct(s.st_mode & 0o777),'device':s.st_dev,'inode':s.st_ino}
checks=[]
def ok(name,val):
 checks.append({'check':name,'passed':bool(val)})
 if not val: raise AssertionError(name)
result=json.loads((P/'RESULT.json').read_text())
ok('final author result pin',sha(P/'RESULT.json')=='fcb1063b957a0b62bcdb8dcba24f40937b2057f604960412f9c905239204749a')
artifacts={}
for key,item in [('source_pins',result['snapshot']['source_pins']),('source_refs',result['snapshot']['targeted_source_refs']),('diff',result['candidate']['diff']),('checks_code',result['bounded_checks']['code']),('checks_result',result['bounded_checks']['result']),('patch_apply_result',result['bounded_checks']['patch_application']),('sourceflow',result['independent_localization'])]:
 p=Path(item['path']); artifacts[key]=record(p)
 ok(key+' exact author hash and bytes',artifacts[key]['sha256']==item['sha256'] and artifacts[key]['bytes']==item['bytes'])
refs=json.loads((P/'SOURCE-REFS.json').read_text())
current_refs={}
for name,item in refs.items():
 p=Path(item['path']); current_refs[name]=record(p)
 ok(name+' current installed dependency hash and bytes',current_refs[name]['sha256']==item['sha256'] and current_refs[name]['bytes']==item['bytes'])
patch=''; files=[]
for item in result['candidate']['files']:
 name=item['relative_path']; oldpath=P/'preimage'/name; newpath=Path(item['candidate_path']); installed=Path(item['installed_path'])
 old=oldpath.read_text(); new=newpath.read_text()
 ok(name+' preimage/candidate/installed final CAS',sha(oldpath)==item['preimage_sha256']==sha(installed) and sha(newpath)==item['candidate_sha256'] and oldpath.stat().st_size==item['preimage_bytes']==installed.stat().st_size and newpath.stat().st_size==item['candidate_bytes'])
 oldtree=ast.parse(old); newtree=ast.parse(new)
 compile(old,str(oldpath),'exec'); compile(new,str(newpath),'exec')
 ok(name+' full syntax compile',True)
 def function(tree,name): return next(n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)
 def loggerinfo(n): return isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='logger.info'
 def dump(n): return ast.dump(n,include_attributes=False)
 if name=='gateway/run_turn.py':
  oldfun=function(oldtree,'_handle_message_with_agent'); newfun=function(newtree,'_handle_message_with_agent')
  oldlog=next(n for n in oldfun.body if loggerinfo(n)); newlog=next(n for n in newfun.body if loggerinfo(n))
  oldfun.body.remove(oldlog); newfun.body.remove(newlog)
  ok(name+' exact AST equality outside one logger statement',dump(oldtree)==dump(newtree))
  ok(name+' eight format placeholders and eight fixed metadata args',newlog.value.args[0].value.count('%')==8 and len(newlog.value.args)==9)
 else:
  oldfun=function(oldtree,'build_turn_context'); newfun=function(newtree,'build_turn_context')
  def span(fun):
   start=next(i for i,n in enumerate(fun.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_preview_text' for t in n.targets))
   end=next(i for i,n in enumerate(fun.body) if i>=start and loggerinfo(n))
   return start,end,fun.body[start:end+1]
  a,b,oldspan=span(oldfun); c,d,newspan=span(newfun)
  ok(name+' original summarizer call retained',dump(oldspan[0])==dump(newspan[0]))
  oldorigin=next(n for n in oldspan if isinstance(n,ast.If)); neworigin=next(n for n in newspan if isinstance(n,ast.If))
  ok(name+' origin interpolation branch exact',dump(oldorigin)==dump(neworigin))
  oldfun.body[a:b+1]=[]; newfun.body[c:d+1]=[]
  ok(name+' exact AST equality outside diagnostic block including original stdout/history/model consumers',dump(oldtree)==dump(newtree))
  fmt=next(n for n in newspan if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='_turn_fmt').value.value
  args=next(n for n in newspan if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='_turn_args').value.elts
  ok(name+' eight base format placeholders and eight metadata args',fmt.count('%')==8 and len(args)==8)
 patch+=''.join(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name))
 files.append({'relative_path':name,'preimage':record(oldpath),'candidate':record(newpath),'installed_current_cas':record(installed)})
ok('supplied patch equals exact two-file source diff',patch==(P/'diff/inbound-metadata-only.patch').read_text())
existing=json.loads((P/'boundedchecks/RESULT.json').read_text())
ok('reuse exact 61 existing source-extracted checks without replay',existing['state']=='PASS_BOUNDED_SOURCE_EXTRACTED_NOT_RUNTIME' and existing['count']==61==len(existing['checks']) and all(c['passed'] for c in existing['checks']))
apply=json.loads((P/'boundedchecks/PATCH-APPLY.json').read_text())
ok('reuse exact successful patch byte-equality result',apply['returncode']==0 and all(f['candidate_byteexact'] for f in apply['files']) and apply['temporary_apply_tree_removed_on_exit'])
ancestors=[Path(x) for x in ['/AGENTS.md','/home/AGENTS.md','/home/jericho/AGENTS.md','/home/jericho/jericho/AGENTS.md','/home/jericho/jericho/Friday_rework/AGENTS.md']]
output={'state':'PASS_INDEPENDENT_SOURCE_STATIC_FINAL_CAS_ONLY','completed_moscow':datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),'checks':checks,'count':len(checks),'candidate_files':files,'artifacts':artifacts,'current_installed_dependency_refs':current_refs,'ancestor_agents_files_present':[str(p) for p in ancestors if p.is_file()],'scope':'Read-only static hash/diff/AST/compile checks. compile() only; no product execution/import/startup. Existing 61 exact-source behavioral checks reused after code/result pins verified; not rerun.','launcher_observation':'Initial python alias absent (exit127), before script execution/artifacts; python3 used once for actual checks.'}
out=R/'STATIC-CHECKS.json'; out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n'); os.chmod(out,0o600)
print(json.dumps({'state':output['state'],'checks':len(checks),'path':str(out),'sha256':sha(out),'ancestor_agents_files_present':output['ancestor_agents_files_present']},ensure_ascii=False))
