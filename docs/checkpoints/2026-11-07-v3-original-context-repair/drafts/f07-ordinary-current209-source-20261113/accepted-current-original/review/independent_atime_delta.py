"""Exact final guard AST control on synthetic stat objects; no filesystem/current call."""
import ast,hashlib,json,types
from pathlib import Path
root=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F07-CURRENT209-PREINTENT-COMPOSITION-20261113')
p=root/'source/current209.py';raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='d6f981a23493f3234dd46595071b0e0f6bc0efb020aa05ca32604c28daca1491'
old=raw.replace(b"identity(canonical_path(source['path']).stat())==identity(info)",b"canonical_path(source['path']).stat()==info")
assert hashlib.sha256(old).hexdigest()=='89b5620bfc20d18c8424c40aeaeaab04ab969ebadcfdf219667f97a50c32905e'
tree=ast.parse(raw);identity=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='identity')
observe=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_observe_current')
guard=next(n for n in observe.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and any(isinstance(a,ast.Constant) and a.value=='F07_FINAL_PROSPECTIVE_SOURCE_CAS_CHANGED' for a in n.value.args))
ns={};exec(compile(ast.Module(body=[identity],type_ignores=[]),'<EXACT_F07_IDENTITY>','exec'),ns)
def need(ok,code):
 if not ok:raise ValueError(code)
base=dict(st_dev=1,st_ino=2,st_uid=1000,st_gid=1000,st_mode=0o100600,st_nlink=1,st_size=1233,st_mtime_ns=5,st_ctime_ns=6,st_atime_ns=7)
info=types.SimpleNamespace(**base);current=types.SimpleNamespace(**dict(base,st_atime_ns=99))
body=b'SYNTHETIC_SOURCE_ONLY';source={'path':'SYNTHETIC_NOT_A_PATH','sha256':hashlib.sha256(body).hexdigest()}
ns.update(need=need,source=source,info=info,canonical_path=lambda path:types.SimpleNamespace(stat=lambda:current),read=lambda path:body,digest=lambda raw:hashlib.sha256(raw).hexdigest())
code=compile(ast.Module(body=[guard],type_ignores=[]),'<EXACT_F07_FINAL_SOURCE_CAS_GUARD>','exec')
rows=[]
def run(name,reject=False):
 try:exec(code,ns)
 except ValueError as e:
  assert reject and str(e)=='F07_FINAL_PROSPECTIVE_SOURCE_CAS_CHANGED'
 else:assert not reject
 rows.append({'name':name,'state':'PASS'})
run('exact_guard_accepts_read_induced_atime_only')
current=types.SimpleNamespace(**dict(base,st_ctime_ns=8));run('exact_guard_rejects_ctime_drift',True)
current=types.SimpleNamespace(**dict(base,st_ino=3));run('exact_guard_rejects_inode_replacement',True)
current=types.SimpleNamespace(**base);ns['read']=lambda path:b'CHANGED';run('exact_guard_rejects_source_content_drift',True)
out=root/'review/FINAL-ATIME-DELTA-CONTROLS.json';out.write_text(json.dumps({'schema':'frw.F07.independent-final-atime-delta-controls.v1','state':'PASS_SOURCE_ONLY_SYNTHETIC','source_sha256':hashlib.sha256(raw).hexdigest(),'previous_source_sha256':hashlib.sha256(old).hexdigest(),'exact_single_source_line_delta_confirmed':True,'count':len(rows),'checks':rows,'actual_guard_lineno':guard.lineno,'H_current_API_new_send_calls':0},indent=2,sort_keys=True)+'\n');out.chmod(0o600)
print(json.dumps({'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'count':len(rows)}))
