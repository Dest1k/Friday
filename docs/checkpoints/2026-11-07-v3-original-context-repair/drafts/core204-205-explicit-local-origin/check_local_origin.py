import ast,copy,datetime,hashlib,importlib.util,json,os,resource,subprocess,time,zlib
from pathlib import Path
from zoneinfo import ZoneInfo
resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));os.umask(0o077)
B=Path(__file__).parent;R=Path('/home/jericho/jericho/Friday_rework');start=time.monotonic();checks=[]
def loadmodule(p,n):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=loadmodule(B/'candidate/frame204/root204_metadata.py','test_root204')
m205=loadmodule(B/'candidate/boundary205/root205_metadata.py','test_root205')
m205.ROOT204_ORIGIN_METADATA=m.reference(B/'candidate/frame204/root204_metadata.py')
policy=json.loads((B/'candidate/frame204/ROOT-204-PUBLIC-ORIGIN-POLICY.json').read_bytes())
env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_AUTHOR_NAME='offline fixture',GIT_AUTHOR_EMAIL='offline@example.invalid',GIT_COMMITTER_NAME='offline fixture',GIT_COMMITTER_EMAIL='offline@example.invalid')
def git(repo,*args,input=None):return subprocess.run(['/usr/bin/git','--no-optional-locks','--no-replace-objects','-C',str(repo),*args],env=env,input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=20).stdout
head=git(R,'rev-parse','HEAD').decode().strip();index=Path(git(R,'rev-parse','--path-format=absolute','--git-path','index').decode().strip());index_before=hashlib.sha256(index.read_bytes()).hexdigest()
def good(name,fn):
 value=fn();checks.append({'name':name,'pass':True});return value
def bad(name,fn,reason=None):
 try:fn()
 except (ValueError,RuntimeError,subprocess.CalledProcessError,OSError) as e:
  if reason is not None:assert reason in str(e),(name,reason,str(e))
  checks.append({'name':name,'pass':True,'observed_refusal':str(e)[:250]});return
 raise AssertionError('unexpected acceptance: '+name)
actual=good('actual_repository_local_committed_main_full489_private28_and_current5',lambda:m.source_origin(head,None,repository=R,provenance_mode='local-committed-main'))
assert actual['fresh_origin_main'] is None and actual['remote_publication']=='DEFERRED_NOT_VERIFIED' and actual['published_snapshot']==policy['published_snapshot']
F=B/'fixtures';F.mkdir(mode=0o700,exist_ok=True);repo=F/'local-main';repo.mkdir(mode=0o700,exist_ok=True);git(repo,'init','--initial-branch=main')
alternates=repo/'.git/objects/info/alternates';alternates.write_text(str(R/'.git/objects')+'\n')
git(repo,'update-ref','refs/heads/main',head)
for name in policy['reviewed_current_files']:
 p=repo/name;p.parent.mkdir(parents=True,mode=0o700,exist_ok=True);p.write_bytes((R/name).read_bytes())
def prove(expected=head,origin=None,mode='local-committed-main'):return m.source_origin(expected,origin,repository=repo,provenance_mode=mode)
proof=good('own_fixture_real_Git_positive_exact_main_and_objects',prove)
git(repo,'update-ref','refs/remotes/origin/main',policy['published_snapshot']);assert prove()==proof
good('stale_local_tracking_ref_is_irrelevant',lambda:prove())
bad('local_mode_refuses_fake_origin_equal_head',lambda:prove(origin=head),'local_mode_has_no_remote_observation')
bad('local_mode_refuses_tracking48_as_origin',lambda:prove(origin=policy['published_snapshot']),'local_mode_has_no_remote_observation')
bad('explicit_unknown_mode_refused',lambda:prove(mode='offline-on-error'),'explicit_provenance_mode_required')
bad('unbound_HEAD_refused',lambda:prove(expected='UNBOUND'),'bound_current_head_required')
bad('historical48_cannot_be_current_authority',lambda:prove(expected=policy['published_snapshot']),'bound_current_head_required')
bad('remote_mode_has_no_automatic_offline_fallback',lambda:prove(mode='published-remote'),'fresh_current_head_origin_required')
remote=good('legacy_remote_local_proof_seam_requires_supplied_matching_observation_not_remote_verification',lambda:prove(origin=head,mode='published-remote'));assert remote['remote_publication']=='FRESH_REMOTE_MAIN_VERIFIED'
bad('legacy_remote_mismatch_refused',lambda:prove(origin=policy['published_snapshot'],mode='published-remote'),'fresh_current_head_origin_required')
(repo/'.git/HEAD').write_text(head+'\n');bad('detached_head_not_local_main',prove);git(repo,'symbolic-ref','HEAD','refs/heads/main')
git(repo,'update-ref','refs/heads/feature',head);git(repo,'symbolic-ref','HEAD','refs/heads/feature');bad('other_branch_not_local_main',prove,'local_committed_main_branch_required');git(repo,'symbolic-ref','HEAD','refs/heads/main')
git(repo,'update-ref','refs/replace/'+head,policy['published_snapshot']);bad('replacement_ref_refused_even_when_Git_ignores_replacements',prove,'replacement_objects_refused');git(repo,'update-ref','-d','refs/replace/'+head)
shallow=repo/'.git/shallow';shallow.write_text(head+'\n');bad('shallow_ancestry_refused',prove,'full_local_ancestry_required');shallow.unlink()
grafts=repo/'.git/info/grafts';grafts.write_text(head+'\n');bad('graft_ancestry_refused',prove,'grafted_ancestry_refused');grafts.unlink()
name=next(iter(policy['reviewed_current_files']));p=repo/name;data=p.read_bytes();p.write_bytes(data+b'\n# drift\n');bad('current_working_bytes_drift_refused',prove,'current_public_working_drift');p.write_bytes(data)
p.unlink();p.symlink_to(R/name);bad('current_working_symlink_refused',prove,'owned_regular_singlelink_required');p.unlink();p.write_bytes(data)
# Real temporary commit objects and refs are created solely in the fixture.
git(repo,'read-tree',head);tree=git(repo,'rev-parse',head+'^{tree}').decode().strip()
unrelated=git(repo,'commit-tree',tree,input=b'no ancestry fixture\n').decode().strip();git(repo,'update-ref','refs/heads/main',unrelated);bad('unrelated_root_commit_refused',lambda:prove(expected=unrelated));git(repo,'update-ref','refs/heads/main',head)
row=m.origin_tree(repo,head)[name];wrongmode='100755' if row[0]=='100644' else '100644';git(repo,'update-index','--cacheinfo',wrongmode,row[2],name);bad_tree=git(repo,'write-tree').decode().strip();modecommit=git(repo,'commit-tree',bad_tree,'-p',head,input=b'wrong mode fixture\n').decode().strip();git(repo,'update-ref','refs/heads/main',modecommit);bad('current_committed_mode_drift_refused',lambda:prove(expected=modecommit),'exact_regular_published_blobs_required');git(repo,'update-ref','refs/heads/main',head);git(repo,'read-tree',head)
blob=git(repo,'hash-object','-w','--stdin',input=b'changed blob fixture\n').decode().strip();git(repo,'update-index','--cacheinfo',row[0],blob,name);bad_tree=git(repo,'write-tree').decode().strip();blobcommit=git(repo,'commit-tree',bad_tree,'-p',head,input=b'wrong blob fixture\n').decode().strip();git(repo,'update-ref','refs/heads/main',blobcommit);bad('current_committed_blob_drift_refused',lambda:prove(expected=blobcommit),'published_blob_changed');git(repo,'update-ref','refs/heads/main',head);git(repo,'read-tree',head)
raw=git(repo,'cat-file','commit',head);objectpath=repo/'.git/objects'/head[:2]/head[2:];objectpath.parent.mkdir(mode=0o700,exist_ok=True);corrupt=raw+b'corrupt\n';objectpath.write_bytes(zlib.compress(b'commit '+str(len(corrupt)).encode()+b'\0'+corrupt));bad('raw_current_commit_identity_refused',prove,'current_commit_object_identity_changed');objectpath.unlink()
# Deterministic moving-HEAD injection calls only real localGit and fabricates no output.
original=m.origin_git;reads=0
def racing(repository,*args,**kw):
 global reads
 if args==('rev-parse','HEAD'):
  reads+=1
  if reads==2:git(repo,'update-ref','refs/heads/main',blobcommit)
 return original(repository,*args,**kw)
m.origin_git=racing;bad('HEAD_movement_during_local_proof_refused',prove,'current_head_changed_during_origin_check');m.origin_git=original;git(repo,'update-ref','refs/heads/main',head)
# Policy/inventory proof failures without changing old immutable evidence.
originalpolicy=m.ORIGIN_POLICY;ownpolicy=B/'fixtures/policy.json';ownpolicy.write_bytes((B/'candidate/frame204/ROOT-204-PUBLIC-ORIGIN-POLICY.json').read_bytes());m.ORIGIN_POLICY=m.reference(ownpolicy);x=json.loads(ownpolicy.read_bytes());x['reviewed_current_files'][name]='0'*64;ownpolicy.write_bytes(m.encoded(x));bad('policy_hash_drift_refused',prove,'reference_hash_changed');m.ORIGIN_POLICY=originalpolicy
# Real fullproof through successor metadata with exact pinned staged204 dependency.
proof205=good('205_pinned204_metadata_fullproof_reuse_actual_repository',lambda:m205.source_origin(head,None,repository=R,provenance_mode='local-committed-main'));assert proof205==actual
snapshot={'head':head,'origin_main':None,'provenance_mode':'local-committed-main','source_origin':actual}
accept204={'public_main_sha':policy['published_snapshot']};accept205={'public_main_sha':None,'source_provenance':{'mode':'local-committed-main','commit':head}}
good('204_snapshot_historical_public48_and_local_current_remain_separate',lambda:m.validate_snapshot_origin(accept204,snapshot))
good('205_snapshot_acceptance_local_commit_and_publication_None',lambda:m205.validate_snapshot_origin(accept205,snapshot))
bad('204_historical_acceptance_cannot_rebind_to_current',lambda:m.validate_snapshot_origin({'public_main_sha':head},snapshot),'accepted204_published_snapshot_required')
bad('205_acceptance_cannot_claim_local_head_as_remote',lambda:m205.validate_snapshot_origin({**accept205,'public_main_sha':head},snapshot),'accepted205_publication_observation_required')
bad('205_acceptance_commit_mismatch_refused',lambda:m205.validate_snapshot_origin({**accept205,'source_provenance':{'mode':'local-committed-main','commit':policy['published_snapshot']}},snapshot),'accepted205_source_provenance_required')
bad('205_snapshot_relabelled_proof_refused',lambda:m205.validate_snapshot_origin(accept205,{**snapshot,'source_origin':{**actual,'published_snapshot':head}}),'exact205_current_origin_proof_required')
bad('205_snapshot_fake_origin_refused',lambda:m205.validate_snapshot_origin({**accept205,'public_main_sha':head},{**snapshot,'origin_main':head}),'local_mode_has_no_remote_observation')
# Extract only changed source-observation prefix, ending before any boot/runtime read.
for version in [204,205]:
 path=B/f'candidate/boundary{version}/core{version}-first-actual-root.py';treeast=ast.parse(path.read_text());fn=next(n for n in treeast.body if isinstance(n,ast.FunctionDef) and n.name=='boundary');prefix=[]
 for node in fn.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='boot' for t in node.targets):break
  prefix.append(node)
 fn=copy.deepcopy(fn);fn.body=prefix+[ast.Return(value=ast.Tuple(elts=[ast.Name(id=n,ctx=ast.Load()) for n in ['head','origin','origin_proof']],ctx=ast.Load()))];mod=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]));seen=[]
 def run(argv,**kw):
  seen.append(argv)
  if 'ls-remote' in argv:raise RuntimeError('offline network call refused before execution')
  return subprocess.run(argv,env=env,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=20)
 ns={'R':repo,'run':run,'require':m.require,'sha':m.sha};exec(compile(mod,str(path),'exec'),ns)
 pins={'execution_provenance_mode':'local-committed-main','execution_public_main_sha':None,'execution_commit':head,'public_changed_files':policy['reviewed_current_files']}
 result=good(f'wrapper{version}_pure_source_prefix_realGit_local_no_remote',lambda:ns['boundary'](m,None,None,pins,None,None,None));assert result[1] is None and not any('ls-remote' in a for a in seen)
 seen.clear();bad(f'wrapper{version}_remote_failure_no_local_fallback',lambda:ns['boundary'](m,None,None,{**pins,'execution_provenance_mode':'published-remote','execution_public_main_sha':head},None,None,None),'offline network call refused');assert len(seen)==2 and 'ls-remote' in seen[-1]
# Every source_ref and embeddedactor/meta/wrapper/template pin, considering futurecanonicalplacement.
rows=json.loads((B/'CANDIDATE-FREEZE.json').read_bytes());mapping={r['destination']:Path(r['staged']) for r in rows};refcount=0
for row in rows:
 path=Path(row['staged']);assert hashlib.sha256(path.read_bytes()).hexdigest()==row['after_sha256']
 if path.suffix=='.json':
  def visit(v):
   global refcount
   if isinstance(v,dict):
    if 'path'in v and 'sha256'in v and isinstance(v['sha256'],str) and len(v['sha256'])==64:
     target=mapping.get(v['path'],Path(v['path']));assert hashlib.sha256(target.read_bytes()).hexdigest()==v['sha256'],(path,v);refcount+=1
    for key,digest in v.get('source_refs',{}).items():assert hashlib.sha256(mapping.get(key,Path(key)).read_bytes()).hexdigest()==digest,(path,key);refcount+=1
    for vv in v.values():visit(vv)
   elif isinstance(v,list):
    for vv in v:visit(vv)
  visit(json.loads(path.read_bytes()))
 else:ast.parse(path.read_text())
good('all_JSON_reference_closure_futurecanonical_paths',lambda:refcount)
for v in [204,205]:
 actor=B/'candidate'/Path('frame204' if v==204 else 'boundary205')/f'run_native{v}_once.py';meta=actor.with_name(f'root{v}_metadata.py');assert hashlib.sha256(meta.read_bytes()).hexdigest() in actor.read_text()
 group=B/f'candidate/boundary{v}';assert hashlib.sha256((group/'SOURCE-PINS.json').read_bytes()).hexdigest() in (group/f'core{v}-first-actual-root.py').read_text()
good('actors_metadata_and_wrappers_manifest_hashes_closed',lambda:True)
assert hashlib.sha256(index.read_bytes()).hexdigest()==index_before
good('real_repository_index_unchanged_after_readonly_controls',lambda:True)
result={'schema':'frw.explicit-local-origin.controls.v1','state':'PASS_SOURCE_ONLY_OFFLINE','at_moscow':datetime.datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),'checks':checks,'check_count':len(checks),'futurecanonical_reference_count':refcount,'actual_local_head':head,'last_verified_historical_published_main':policy['published_snapshot'],'actual_local_proof':actual,'network_commands_executed':0,'actual_wrapper_preflight_runs':0,'services_DB_native_install_Office_model_Telegram_effects':0,'fixture_bytes':sum(p.stat().st_size for p in F.rglob('*') if p.is_file()),'elapsed_seconds':time.monotonic()-start,'limits':{'wall_seconds':90,'CPU_seconds':60,'address_space_bytes':512*1024**2},'claims':'Source-only localGit proof controls and isolated AST source-prefix consumers. Supplied legacy matching observation is not fresh remote verification. Actual full wrappers/gates/installed/H not executed.'}
assert result['fixture_bytes']<64*1024**2
(B/'CONTROLS.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');(B/'CONTROLS.json').chmod(0o600)
print(json.dumps({'state':result['state'],'check_count':len(checks),'refs':refcount,'head':head,'elapsed':result['elapsed_seconds']}))
