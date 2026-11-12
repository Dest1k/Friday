"""Independent affected-area check of final three-footer exact-path-type repair."""
import ast, datetime, hashlib, json, os, re, stat, tempfile
from pathlib import Path
HERE=Path(__file__).absolute().parent
R=HERE.parent
EXPECTED='fdf8a2e498220b3020e8e73be71d68e8640f077205c0c6c2762762d1fc4eebf9'
OLD=R/'pre-review-source-cc6f9c98'
os.umask(0o077)
checks=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def good(n,v=True):
    assert v,n
    checks.append(n)
def refused(n,fn):
    try:fn()
    except Exception:
        checks.append(n)
        return
    raise AssertionError(n)
def defs(raw):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)}
def select(raw,names,ns):
    nodes=[n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<review-affected-inert-functions-only>','exec'),ns)
    return ns
freeze_raw=(R/'SOURCE-FREEZE.json').read_bytes()
good('final_freeze_pin',sha(freeze_raw)==EXPECTED)
freeze=json.loads(freeze_raw)
oldfreeze_raw=(OLD/'SOURCE-FREEZE.json').read_bytes()
good('prior_freeze_pin',sha(oldfreeze_raw)=='cc6f9c9868f6d176fb36692d192be904ca6d41ab4ea63ae5ae41d3704a8bdcc0')
delta=[]
for name,pin in freeze['files'].items():
    raw=(R/'candidate'/name).read_bytes()
    good(name+':final_exact_pin',len(raw)==pin['bytes'] and sha(raw)==pin['sha256'])
    old=(OLD/'candidate'/name).read_bytes()
    if old!=raw:
        delta.append(name)
        oldtext,newtext=old.decode(),raw.decode()
        good(name+':only_exact_path_str_predicate_added',newtext==oldtext.replace("and type(reference['bytes']) is int", "and type(reference['path']) is str and type(reference['bytes']) is int"))
good('only_three_footers_changed',sorted(delta)==[b+'/f06_footer.py.txt' for b in ('correct','first','wrong-edit')])
class Refused(Exception):pass
full=(R/'checks/first/SYNTHETIC-full-consumer.py').read_bytes()
base=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py').read_bytes()
good('original_fullv42_source_pin',sha(base)=='f0caba28ba9e823574a5149b55989aea7f4e5c893c3a89a7b4eb0ed0cf5e7ad3')
good('safe_read_and_symlink_AST_unchanged',all(defs(base)[n]==defs(full)[n] for n in ('safe_read','no_symlinks')))
nsbase=select(full,{'safe_read','no_symlinks'},dict(Path=Path,os=os,stat=stat,MAX_JSON=1048576,Refused=Refused))
payload=b'SYNTHETIC-REVIEW-ONLY\n'+b'X'*1250000
helpers={'_f06_need','_f06_path','_f06_reference_read','_f06_bounded_reference_read'}
for branch in ('first','correct','wrong-edit'):
    raw=(R/'candidate'/branch/'f06_footer.py.txt').read_bytes()
    oldraw=(OLD/'candidate'/branch/'f06_footer.py.txt').read_bytes()
    common=dict(nsbase,re=re,digest=sha)
    new=select(raw,helpers,dict(common))
    old=select(oldraw,helpers,dict(common))
    with tempfile.TemporaryDirectory(prefix='synthetic-path-guard-',dir=HERE) as tmp:
        p=Path(tmp)/'SYNTHETIC-large.bin'
        p.write_bytes(payload);p.chmod(0o600)
        ref=dict(path=str(p),bytes=len(payload),sha256=sha(payload))
        bounded=new['_f06_bounded_reference_read']
        good(branch+':final_str_reference_gt1MiB',bounded(ref)==payload)
        good(branch+':prior_Path_reference_gap_reproduced',old['_f06_bounded_reference_read'](dict(ref,path=p))==payload)
        refused(branch+':present_Path_reference_refused',lambda:bounded(dict(ref,path=p)))
        small=p.with_name('SYNTHETIC-small.bin');small.write_bytes(b'SYNTHETIC');small.chmod(0o600)
        good(branch+':path_reader_Path_ABI_preserved',new['_f06_reference_read'](small)==b'SYNTHETIC')
        refused(branch+':default_path_reader_stays1MiB',lambda:new['_f06_reference_read'](p))
        for label,value in [('bool',True),('zero',0),('over_cap',24*1024**2+1),('short',len(payload)-1),('long',len(payload)+1)]:
            refused(branch+':declared_'+label+'_refused',lambda v=value:bounded(dict(ref,bytes=v)))
        refused(branch+':wrong_sha_refused',lambda:bounded(dict(ref,sha256='0'*64)))
        refused(branch+':aliased_path_refused',lambda:bounded(dict(ref,path=str(p.parent)+'/./'+p.name)))
        p.chmod(0o640)
        refused(branch+':private0640_refused',lambda:bounded(ref));p.chmod(0o600)
        link=p.with_name('SYNTHETIC-hardlink');os.link(p,link)
        refused(branch+':hardlink_refused',lambda:bounded(ref));link.unlink()
        link=p.with_name('SYNTHETIC-symlink');link.symlink_to(p)
        refused(branch+':symlink_refused',lambda:bounded(dict(ref,path=str(link))))
result=dict(schema='frw.F06.R2.independent-path-guard-delta.v1',status='PASS',source_freeze_sha256=EXPECTED,prior_source_freeze_sha256='cc6f9c9868f6d176fb36692d192be904ca6d41ab4ea63ae5ae41d3704a8bdcc0',changed_source_files=delta,checks=checks,count=len(checks),actual_runtime_acceptance=False,actual_payload_reads=False,external_effects=False,extracted_functions_only=True,timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat())
out=HERE/'FINAL-PATH-GUARD-CONTROLS.json'
out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');out.chmod(0o600)
print(json.dumps(dict(path=str(out),sha256=sha(out.read_bytes()),controls=len(checks))))
