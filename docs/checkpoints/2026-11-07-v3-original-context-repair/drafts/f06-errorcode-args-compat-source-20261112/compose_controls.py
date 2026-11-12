"""Bounded own source composition checks, no application/native imports."""
import os
os.umask(0o077)
import ast,difflib,hashlib,json,pathlib,resource,subprocess,sys,tempfile,time
B=pathlib.Path(__file__).resolve().parent
R=B/'revision2';pins=json.loads((R/'SOURCE-PINS.json').read_text());started=time.monotonic();os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
checks=[]
def ok(n,v):assert v,n;checks.append({'name':n,'pass':True})
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
for row in pins['rows']:
 ok('exact_before_'+row['relative'],sha(row['before']['path'])==row['before']['sha256'])
 ok('exact_after_'+row['relative'],sha(row['after']['path'])==row['after']['sha256'])
 src=pathlib.Path(row['after']['path']).read_text();ast.parse(src,feature_version=(3,12));ok('Python312_grammar_'+row['relative'],True)
 if not row['changed']:ok('unchanged_actual_caller_'+row['relative'],row['before']['sha256']==row['after']['sha256'])
helper=ast.parse((R/'candidate/request_args_compat_v2.py').read_text());probe=ast.parse((R/'candidate/conversion_probe.py').read_text())
def constant(tree,name):return ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id==name for x in n.targets)))
ok('helper_probe_six_exact_names_join',constant(helper,'REQUEST_NAMES')==constant(probe,'_COMPAT_NAMES') and len(constant(helper,'REQUEST_NAMES'))==6)
old=ast.parse((B/'baseline/conversion_probe.py').read_text())
a=next(n for n in old.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='_COMPAT_NAMES' for x in n.targets));a.value=next(n.value for n in probe.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='_COMPAT_NAMES' for x in n.targets))
# Docstring wording changes only; every operational probe statement remains exact.
for t in (old,probe):
 cls=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='OneShotConversionProbe');cls.body.pop(0)
ok('probe_only_token_arity_and_doc_change',ast.dump(old,include_attributes=False)==ast.dump(probe,include_attributes=False))
# Validate all eleven original source files used by future unchanged caller graph; references only, not a frame clone.
T=pathlib.Path('/home/jericho/.cache/FRW-SOL-V3-F06-ONE-TEMPLATE-DIAGNOSTIC-FRAME-20261112');freeze=json.loads((T/'SOURCE-FREEZE-FINAL.json').read_text());full=[]
for row in freeze['files']:
 p=pathlib.Path(row['path'])
 if p.parent==T/'candidate' and p.suffix=='.py':
  ok('Task25_original_source_'+p.name,sha(p)==row['sha256']);over=R/'candidate'/p.name;out=over if over.exists() else p
  full.append({'name':p.name,'origin':row,'after':{'path':str(out),'sha256':sha(out),'bytes':out.stat().st_size},'changed':sha(out)!=row['sha256']})
ok('full_frame_map_11_existing_2_changed_9_unchanged',len(full)==11 and sum(x['changed'] for x in full)==2)
(R/'PROPOSED-FRAME-SOURCE-MAP.json').write_text(json.dumps({'state':'SOURCE_MAP_ONLY_ROOT_MUST_CREATE_FRESH_REVISION_NO_AUTHORITY','files':full,'new_runtime_grant':False,'old_consumed_operation_reused':False},indent=2)+'\n')
# Real forward/reverse patch application only against tiny own fivefile stand.
with tempfile.TemporaryDirectory(dir=B,prefix='patch-stand-') as d:
 stand=pathlib.Path(d)
 for row in pins['rows']:(stand/row['relative']).write_bytes(pathlib.Path(row['before']['path']).read_bytes())
 patch=R/'ERRORCODE-ARGS-COMPAT.patch'
 for reverse,label,target in ((False,'forward','after'),(True,'reverse','before')):
  argv=['/usr/bin/patch','--batch','--fuzz=0','-p1','--input',str(patch)]+(['--reverse'] if reverse else [])
  p=subprocess.run(argv,cwd=stand,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15)
  ok('real_patch_'+label,p.returncode==0 and all(sha(stand/row['relative'])==row[target]['sha256'] for row in pins['rows']))
  (R/(label+'-patch-stdout.txt')).write_bytes(p.stdout);(R/(label+'-patch-stderr.txt')).write_bytes(p.stderr)
 # Corrupt expected preimage and assert this exact patch cannot silently apply.
 row=next(x for x in pins['rows'] if x['changed']);p=stand/row['relative'];p.write_text('foreign source\n')
 p=subprocess.run(['/usr/bin/patch','--batch','--fuzz=0','-p1','--dry-run','--input',str(patch)],cwd=stand,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15)
 ok('wrong_preimage_patch_refused',p.returncode!=0)
ok('temporary_stand_removed',not pathlib.Path(d).exists())
report={'schema':'task27.composition.v1','scope':'SOURCE_ONLY_NO_APP','checks':checks,'count':len(checks),'all_pass':True,'observed_wall_seconds':time.monotonic()-started,'caps':{'inherited_CPU':60,'inherited_AS':536870912,'affinity':sorted(os.sched_getaffinity(0)),'patch_wall_each':15,'outer_wall_enforced_by_parent':90},'all_patch_children_waited':True}
(R/'COMPOSITION-CHECKS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'count':len(checks),'all_pass':True,'wall':report['observed_wall_seconds']}))
