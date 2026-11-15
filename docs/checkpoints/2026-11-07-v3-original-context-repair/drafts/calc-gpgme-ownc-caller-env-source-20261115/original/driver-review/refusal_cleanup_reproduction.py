"""Pure reproduction: execute only extracted wrapper finally with no GDB."""
import ast
import hashlib
import json
from pathlib import Path
ROOT=Path('/home/jericho/.cache/FRW-ASTRA-GPGME-OWNC-CALLER-SOURCE-20261115')
p=ROOT/'driver/ownc_gdb.py';raw=p.read_bytes();tree=ast.parse(raw)
run=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='run')
body=next(x.finalbody for x in run.body if isinstance(x,ast.Try))
cleanup=ast.parse('cleanup_reached=True')
ns={'STATE':{'error':'original_refusal'},'CFG':{'native_observer_ref':{'path':'source-placeholder'}},'final':cleanup}
def broken_diagnostic():raise OSError('pure_synthetic_diagnostic_failure')
ns['capture_refusal_stop']=broken_diagnostic
exception=None
try:exec(compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),str(p),'exec'),ns)
except Exception as exc:exception=type(exc).__name__
out={'source_ref':{'path':str(p),'sha256':hashlib.sha256(raw).hexdigest()},'diagnostic_exception_class':exception,'cleanup_reached':ns.get('cleanup_reached',False),'first_error':ns['STATE']['error'],'recorded_diagnostic_exception_class':ns['STATE'].get('ownc_refusal_diagnostic_exception_class'),'scope':'PURE_EXTRACTED_WRAPPER_FINALLY_NO_TARGET_OR_GDB'}
q=ROOT/'driver-review/refusal-cleanup-final-delta.json';q.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');q.chmod(0o600)
print(json.dumps(out,sort_keys=True))
