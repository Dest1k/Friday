'Pure metadata observer/join for a later Root-owned genuine210 to211 boundary.\nImport performs no product read, collector, consumer call, request or grant. The optional\nCLI can only exclusively write its own bound metadata after Root supplies actual files.\nSource/projection, historical closure, current observations and fresh authority are distinct.\n'
from pathlib import Path
import argparse,copy,datetime,hashlib,json,os,stat,time
B=Path(__file__).resolve().parent
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
S=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-R02-FINAL211-COHERENT-COMPOSITION-20261113')
S210=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-SOURCE39-EXACT209-SUCCESSOR-PREP-20261113')
P=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-SOURCE39-EXACT209-SUCCESSOR-PREP-20261113/project501')
C=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-R02-FINAL211-COHERENT-COMPOSITION-20261113/project503')
LAYER='r02-telegram-text-uncertain-recovery-after-source210'
BEFORE_RECEIPT='99b940361483584a851f0baf1054b5bed61e0141a3bb11cf4a94a4e75bbc0629'
PREVIOUS_INPUT='f649948a3176d6a258adc1ea1306889ee9d4d2d52e11fcccb1094b00d1b846ed'
EXPECTED_RECEIPT='1901e38b880b77394cd313a049f1b6918d87f47a51df1fbc23315d5780a7706a'
ROOT198={'path': '/home/jericho/.cache/FRW-ASTRA-V3-DSH-COHERENT-ROOT-COMPOSITION-20261111/final-v1/fresh-source-request/REQUEST.json', 'sha256': '886c6ab5bc76a810b24004f7042ef7c1b5add1b78f04781fac9c96335e3bd448'}
# Existing immutable source evidence plus closed actual210 history; no fresh runtime grant.
FIXED={'native_spec': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-R02-FINAL211-COHERENT-COMPOSITION-20261113/FINAL-NATIVE-SPEC.json', 'sha256': '1c1c6447203766536d21cee4b0f609fceb2f66196319c8948525788cd3f00083'}, 'source_freeze': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-R02-FINAL211-COHERENT-COMPOSITION-20261113/SOURCE-PINS.json', 'sha256': '79775d8ee2173ddde2345069780287f62fba747cd50146e141cc3a94b5e56a60'}, 'prospective_composition': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-R02-FINAL211-COHERENT-COMPOSITION-20261113/NATIVE211-PROSPECTIVE-COMPOSITION.json', 'sha256': '194b437e44e281c3d5d4eb668b8e14e59ec55695fcff6ed7b754095c78c8306d'}, 'project_origins': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-R02-FINAL211-COHERENT-COMPOSITION-20261113/PROJECT503-ORIGINS.json', 'sha256': '4d65e3851d4f511790420a92fb1f590502a12d87fe931c84c0b9624aa66fd4e9'}, 'public_origins': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-R02-FINAL211-COHERENT-COMPOSITION-20261113/PUBLIC503-ORIGINS.json', 'sha256': '6f509d01974b2b68148966dffaedba18388916287fe38b2e0f911cb7ec94bab7'}, 'prospective_private_input': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-R02-FINAL211-COHERENT-COMPOSITION-20261113/INPUT-SOURCE211.PROSPECTIVE.NOT_INSTALLED.json', 'sha256': '6b8bbd7719a6e09ece57ba122c4083598d78f3d03dc1c96178d770599dfcb5bd'}, 'prospective_public_input': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-R02-FINAL211-COHERENT-COMPOSITION-20261113/INPUT-SOURCE211.PUBLIC.PROSPECTIVE.NOT_INSTALLED.json', 'sha256': '195485b691540a12eaca1dc71603b974797bdbe52e0276137039398e0a2ed86b'}, 'source_result': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-R02-FINAL211-COHERENT-COMPOSITION-20261113/RESULT.json', 'sha256': 'cc50d143ac75eed51d692a9c1c21b4f04c9b9d9241dc9a5085e12a59ffd2baa9'}, 'prepared_root_recipe': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-R02-FINAL211-COHERENT-COMPOSITION-20261113/ROOT-NEXT-RECIPE.json', 'sha256': '275fbd098ab9d3467a3d5f18218d033899c000edab76837708ed9b5e7b829f95'}, 'composition_journal_checks': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-R02-FINAL211-COHERENT-COMPOSITION-20261113/COMPOSITION-AND-JOURNAL-CHECKS.json', 'sha256': '9780760dd3916ee17a39b289df414d57cb896aae9b98961215e6164c95ff9364'}, 'metadata_consumer_checks': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-R02-FINAL211-COHERENT-COMPOSITION-20261113/METADATA-CONSUMER-CHECKS.json', 'sha256': 'a97abbf36d153b8a1d577a8d3c019b0f494b96ac6bd91edd4721ab3107cee0cf'}, 'final_readback': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-R02-FINAL211-COHERENT-COMPOSITION-20261113/FINAL-READBACK-AND-CLEANUP.json', 'sha256': 'f6b8e8769007a957dcaf16a4ebac6bcd04258dec11653282c42a5475f6b38591'}, 'independent_source_review': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-R02-FINAL211-COHERENT-COMPOSITION-20261113/review/RESULT.json', 'sha256': '1894f006d931dc2235b6e409331b9a436b87fb458c4ac9acffcad024d8153351'}, 'recipe_supplement_review': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-R02-FINAL211-COHERENT-COMPOSITION-20261113/review/RECIPE-SUPPLEMENT-REVIEW.json', 'sha256': '8efcce9fc85a2e026b82f97743ae337dab4bbcadaa47b0e6e8c07a3cc9550b03'}, 'inherited_private_limit': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-R02-FINAL211-COHERENT-COMPOSITION-20261113/INHERITED-PRIVATE-PREREQUISITE-LIMIT.json', 'sha256': '83d80f67226339692f1055124de2d87636660e9b90e3dc62dce02a164264f651'}, 'actual210_closure': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-CORE210-ROOT-20261113/ACTUAL210-INSTALLED-CLOSED.json', 'sha256': 'a8763c46130e8095cd67985a9781a5e91f2d5cf4767f4399739b5ceba8b2796e'}, 'pm_environment_basis': {'path': '/home/jericho/.cache/FRW-SOL-V3-CORE204-RTF-READER-COMPOSITION-20261111/READONLY-PM-ENVIRONMENT-BASIS.json', 'sha256': '2ab5df26d6bd153ccc175e5813ad0fd769be377611b653fee486e3c3fab2062e'}}
ORIGINAL210_INPUT={'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-SOURCE39-EXACT209-SUCCESSOR-PREP-20261113/INPUT-SOURCE210.PROSPECTIVE.NOT_INSTALLED.json', 'sha256': 'f649948a3176d6a258adc1ea1306889ee9d4d2d52e11fcccb1094b00d1b846ed'}
CURRENT211_INPUT=dict(FIXED['prospective_private_input'])
ORIGINAL210_ORIGIN_POLICY={'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE210-ROOT-FRAME-PREP-20261113/ROOT-210-PUBLIC-ORIGIN-POLICY.json', 'sha256': '3fad753118d1bee732ae56c54213c5b808414748e06b460226de3b9efb81c099'}
PROFILE_SOURCE_JOIN={'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT207-ROOT-SOURCE-AFTER206-20261112/PROFILE-SOURCE-JOIN.json', 'sha256': '9d1c1e6fdaadc68f07eba2425007071cc14bae4c80af203f9b37d54587e53746'}
COMPLETED210_SOURCE_COMMIT='4731fc41d0ccac05c965313a5d0b7da06c0ac078'
PUBLIC5={'scripts/friday_ordinary_install.py': '4898cb6a949656b27507db90ae1de173deb710e90dd401c4dd5b615732708605', 'docs/checkpoints/2026-11-07-v3-original-context-repair/build-layer-publication-request.py': 'd0aee45fbcb5e8ef532ad7b400b893c8520a36f590077f54f4c94cb3b695e10d', 'docs/checkpoints/2026-11-07-v3-original-context-repair/friday_v3_layer_publication.py': '7a8a9f260f52ddbc3131304b2f82d72cf17cb557cb7453d98fae288d2e76c008', 'patches/hermes/r02-telegram-text-uncertain-recovery-after-source210.patch': 'f95ea4ba023aff1cc43d66f5417fbbdcfbe3cd0dc15150faeeb526a59ba176c6', 'patches/hermes/r02-telegram-text-uncertain-recovery-after-source210-manifest.json': '082eec729d3006543784e3e882266409161930e514ee3bcc75460959e5ddff7c'}
PUBLIC5_MODES={name:('100755'if name.endswith('/friday_v3_layer_publication.py')else'100644')for name in PUBLIC5}
HISTORICAL210_REFS={'source_receipt': {'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/preparation/ordinary-source-update-v45-c90abf9e120291f1/hermes-agent.source.json', 'sha256': '99b940361483584a851f0baf1054b5bed61e0141a3bb11cf4a94a4e75bbc0629'}, 'marker': {'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/preparation/ordinary-source-update-v45-c90abf9e120291f1/FRIDAY-INSTALL.json', 'sha256': 'd72d057d945882d5f780b46befe598f65f6910198fa25c67ac26d725710d8f58'}, 'stamp': {'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/preparation/ordinary-source-update-v45-c90abf9e120291f1/install-stamp.json', 'sha256': '8c3f000a8e5112562bd75cc7110ec78822892a31501ed1c7f8b57a59f0f44154'}, 'request': {'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/preparation/ordinary-source-update-v45-c90abf9e120291f1/request.json', 'sha256': 'c90abf9e120291f1ad52e0ace36dad7c34f86956096da65d34dc6f2990a64f23'}, 'committed': {'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/preparation/ordinary-source-update-v45-c90abf9e120291f1/committed.json', 'sha256': '28f156bd70ce453687d94608ca612a8750ee10e20bf04131f4a917cb2e105387'}, 'intent': {'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/preparation/ordinary-source-update-v45-c90abf9e120291f1/intent.json', 'sha256': '93b8a95b2b41e1f406314653948d1ab6aed37cb7797c8a1b6df9c673e5251a95'}, 'complete_closure': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-CORE210-ROOT-20261113/ACTUAL210-INSTALLED-CLOSED.json', 'sha256': 'a8763c46130e8095cd67985a9781a5e91f2d5cf4767f4399739b5ceba8b2796e'}, 'root_journal': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE210-ROOT-FRAME-PREP-20261113/ROOT-NATIVE210-LIVE-OPERATION.json', 'sha256': '3cfb7ad9e64a07113f5412fdc723e11e80fa3e1d8d0d64068e510320c269d3a9'}, 'root_return': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE210-ROOT-FRAME-PREP-20261113/FUTURE-EXECUTION/RETURN.json', 'sha256': '9dc5a36a525a9763123e47e938862fcf9ee051bcee5bd99d9834509d9220756b'}, 'actual209_predecessor': {'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/preparation/ordinary-source-update-v45-6f3688ddccbfa2ff/request.json', 'sha256': '6f3688ddccbfa2ffca84129ea96177f42c594feddbb530eeb99ce5c362ed07b6'}, 'accepted210_source_manifest': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE210-ROOT-FRAME-PREP-20261113/SOURCE-PINS.json', 'sha256': 'dda5b32114b401e0159b237145d3bfa0fed720ae1a45c85f9f4e98a00c0ffc19'}}
SNAPSHOT_TRUE_FIELDS=(
 'source_authority_verified','public_source_pins_verified','operational_source_pins_verified',
 'profile_routing_verified','process_environment_verified','ordinary_readonly_quiescent',
 'all_three_user_db_zero_leases','stop_cooldown_clear','sole_heavy_slot_clear',
 'no_current_maintenance','cancellation_clear','resources_sufficient',
 'all_profile_owned_work_quiescent','current_request_unconsumed','old_effects_not_replayed',
 'native_pm_selected_python_verified','product_services_healthy_infinite_lifetime',
 'unchanged_bank_profile_evidence_reusable','known_limits_retained','current_resume_turn_and_delivery_conflict_free')
class InvalidBinding(ValueError):pass
def require(value,reason):
 if not value:raise InvalidBinding(reason)
def encoded(value):return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def owned(path):
 p=Path(path);v=p.lstat()
 require(stat.S_ISREG(v.st_mode) and not p.is_symlink() and v.st_uid==os.getuid() and v.st_nlink==1,'owned_regular_singlelink_required:'+str(p))
 # Historical0664 is accepted under protected home after identity/hash validation.
 for parent in p.parents:
  if parent==Path('/'):break
  w=parent.lstat();require(stat.S_ISDIR(w.st_mode) and not parent.is_symlink(),'real_parent_required')
 return p

def reference(path):return {'path':str(path),'sha256':sha(owned(path))}
def readref(ref):
 require(type(ref) is dict and set(ref)=={'path','sha256'},'exact_reference_fields_required')
 require(type(ref['path']) is str and Path(ref['path']).is_absolute() and type(ref['sha256']) is str and len(ref['sha256'])==64 and all(c in '0123456789abcdef'for c in ref['sha256']),'bound_absolute_sha256_reference_required')
 p=owned(ref['path']);require(sha(p)==ref['sha256'],'reference_hash_changed:'+str(p));return json.loads(p.read_bytes())
def read_sized_source_ref(ref):
 # Only the closed source-gate producer shape is admitted here. General Root
 # refs keep readref's exact two-field contract and all existing path checks.
 require(type(ref)is dict and set(ref)=={'path','sha256','bytes'},'exact_sized_source_reference_fields_required')
 require(type(ref['bytes'])is int and ref['bytes']>0,'positive_sized_source_reference_bytes_required')
 plain={'path':ref['path'],'sha256':ref['sha256']}
 readref(plain)
 raw=owned(ref['path']).read_bytes()
 require(len(raw)==ref['bytes'],'sized_source_reference_byte_length_changed')
 require(hashlib.sha256(raw).hexdigest()==ref['sha256'],'sized_source_reference_hash_changed')
 return json.loads(raw)
def fresh(value,now,reason):
 try:
  instant=datetime.datetime.fromisoformat(value);require(instant.utcoffset() is not None,'timezone_required')
  age=now-instant.timestamp();require(0<=age<=300,reason)
 except (ValueError,TypeError,OverflowError) as e:raise InvalidBinding(reason) from e


def origin_git(repository, *args, input=None):
 import subprocess
 # Never use replacement objects, optional index writes or a network operation here.
 env=dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1')
 return subprocess.run(['/usr/bin/git','--no-optional-locks','--no-replace-objects',
                        '-C',str(repository),*args], input=input,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                       timeout=20,check=True,env=env).stdout

def git_oid(kind, raw):
 return hashlib.sha1(kind.encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def origin_tree(repository, commit):
 raw=origin_git(repository,'ls-tree','-rz','--full-tree',commit)
 rows={}
 for record in raw.split(b'\0'):
  if not record:continue
  header,name=record.split(b'\t',1);mode,kind,oid=header.decode().split()
  name=name.decode('utf-8');require(name not in rows,'duplicate_git_path')
  rows[name]=(mode,kind,oid)
 return rows

def origin_blobs(repository, tree, expected, modes=None):
 names=sorted(expected)
 modes={name:'100644' for name in names} if modes is None else modes
 require(set(modes)==set(expected) and all(mode in ('100644','100755') for mode in modes.values()),'exact_regular_git_modes_required')
 require(all(name in tree and tree[name][:2]==(modes[name],'blob') for name in names),
         'exact_regular_published_blobs_required')
 oids=[tree[name][2] for name in names]
 raw=origin_git(repository,'cat-file','--batch',input=('\n'.join(oids)+'\n').encode())
 offset=0
 for name,oid in zip(names,oids):
  end=raw.index(b'\n',offset);header=raw[offset:end].decode().split();offset=end+1
  require(len(header)==3 and header[:2]==[oid,'blob'],'exact_git_blob_header_required')
  size=int(header[2]);body=raw[offset:offset+size];offset+=size
  require(raw[offset:offset+1]==b'\n' and len(body)==size,'complete_git_blob_required');offset+=1
  require(git_oid('blob',body)==oid,'git_blob_object_identity_changed')
  require(hashlib.sha256(body).hexdigest()==expected[name],'published_blob_changed:'+name)
 require(offset==len(raw),'unexpected_git_batch_tail')

def source_binding_refs(acceptance=None):
 acceptance=readref(reference(B/'ROOT-211-SOURCE-ACCEPTANCE.json'))if acceptance is None else acceptance
 require(type(acceptance)is dict,'Root_source_acceptance_object_required')
 refs={name:acceptance[name]for name in ('origin_policy','project_source_proof')}
 require(refs['origin_policy']['path']==str(B/'ROOT-211-PUBLIC-ORIGIN-POLICY.json')and refs['project_source_proof']['path']==str(B/'ROOT-211-PROJECT-SOURCE.json'),'own_Root_source_binding_paths_required')
 return refs

def origin_policy(acceptance=None):
 acceptance=readref(reference(B/'ROOT-211-SOURCE-ACCEPTANCE.json'))if acceptance is None else acceptance
 refs=source_binding_refs(acceptance);policy=readref(refs['origin_policy']);old=readref(ORIGINAL210_ORIGIN_POLICY)
 require(policy['schema']=='frw.root211.raw-git-full-counterpart-origin-policy.v1'and policy['execution_grant']is False and policy['template_only_no_execution_grant']is False,'actual_Root211_source_origin_policy_required')
 require(policy['predecessor210_origin_policy']==ORIGINAL210_ORIGIN_POLICY and policy['completed210_source_commit']==COMPLETED210_SOURCE_COMMIT,'exact_completed210_source_origin_required')
 for key in ('published_ancestor48_policy','completed205_public_input','completed205_source_commit','completed206_public_input','completed206_source_commit','completed207_public_input','completed207_source_commit','completed208_public_input','completed208_source_commit','completed209_public_input','completed209_source_commit'):
  require(policy[key]==old[key],'unchanged_ancestral_origin_policy_required:'+key)
 require(policy['completed210_public_input']==old['current_public_input'],'exact_completed210_public501_required')
 require(policy['current_private_project']==str(C)and policy['expected_actual_input']==CURRENT211_INPUT and policy['previous_input']==ORIGINAL210_INPUT,'exact211_private_source_domain_required')
 require(policy['current_public_input']==FIXED['prospective_public_input']and policy['private_origins']==FIXED['project_origins']and policy['public_origins']==FIXED['public_origins'],'exact211_source_origins_required')
 require(policy['reviewed_current_files']==PUBLIC5 and policy['reviewed_current_modes']==PUBLIC5_MODES,'exact211_public5_policy_required')
 require(policy['source_commit']==acceptance['source_provenance']['commit'],'exact211_Root_commit_policy_join_required')
 require(policy['public_helper_sha256']==PUBLIC5['scripts/friday_ordinary_install.py']and policy['private_helper_sha256']=='ce115948ae7a0ee577f9ec72d1bcce0f7f71deb6ce4255a281c28461dc64604b','exact211_distinct_helpers_required')
 require(policy['expected211_receipt_sha256']==EXPECTED_RECEIPT,'projection_only_receipt_pin_required')
 return policy

def source_origin(expected_head, fresh_origin, *, repository=None, provenance_mode='published-remote', acceptance=None):
 repository=Path(repository)if repository is not None else Path('/home/jericho/jericho/Friday_rework')
 policy=origin_policy(acceptance);old=readref(policy['published_ancestor48_policy']);validate_project_binding(acceptance)
 require(type(expected_head)is str and len(expected_head)==40 and all(c in '0123456789abcdef'for c in expected_head),'bound_current_head_required')
 head=origin_git(repository,'rev-parse','HEAD').decode().strip()
 require(head==expected_head and provenance_mode in ('published-remote','local-committed-main'),'bound_current_head_mode_required')
 if provenance_mode=='published-remote':require(head==fresh_origin,'fresh_current_head_origin_required')
 else:
  require(fresh_origin is None,'local_mode_has_no_remote_observation')
  require(origin_git(repository,'symbolic-ref','-q','HEAD').strip()==b'refs/heads/main'and origin_git(repository,'rev-parse','refs/heads/main').decode().strip()==head,'local_committed_main_required')
 require(not origin_git(repository,'for-each-ref','--format=%(refname)','refs/replace/').strip(),'replacement_objects_refused')
 require(origin_git(repository,'rev-parse','--is-shallow-repository').strip()==b'false','full_local_ancestry_required')
 graft=Path(origin_git(repository,'rev-parse','--path-format=absolute','--git-path','info/grafts').decode().strip());require(not os.path.lexists(graft),'grafted_ancestry_refused')
 for commit in [head,old['published_snapshot'],policy['completed205_source_commit'],policy['completed206_source_commit'],policy['completed207_source_commit'],policy['completed208_source_commit'],policy['completed209_source_commit'],policy['completed210_source_commit']]:
  require(git_oid('commit',origin_git(repository,'cat-file','commit',commit))==commit,'raw_commit_identity_changed');origin_git(repository,'merge-base','--is-ancestor',commit,head)
 ancestor=readref(old['public_input'])['project_files'];require(len(ancestor)==489,'exact48public489_required')
 oldtree=origin_tree(repository,old['published_snapshot']);origin_blobs(repository,oldtree,ancestor);origin_blobs(repository,oldtree,old['snapshot_guards'],old['snapshot_guard_modes'])
 for name,row in old['retained_executed_sources'].items():require(reference(row['path'])=={k:row[k]for k in ('path','sha256')}and row['sha256']==old['snapshot_guards'][name],'old48_executed_source_join_changed')
 for number,count in [(205,491),(206,493),(207,495),(208,497),(209,499),(210,501)]:
  prior=readref(policy['completed'+str(number)+'_public_input'])['project_files'];require(len(prior)==count,'exact_predecessor_public_inventory_required');origin_blobs(repository,origin_tree(repository,policy['completed'+str(number)+'_source_commit']),prior)
 public=readref(policy['current_public_input'])['project_files'];private=readref(CURRENT211_INPUT)['project_files'];spec=readref(FIXED['native_spec'])
 require(set(public)==set(private)and len(public)==503,'exact211public_private503_required')
 differences=sorted(name for name in public if public[name]!=private[name])
 require(differences==spec['private_difference_names']and len(differences)==spec['private_difference_count']==28,'exact28_private_public_differences_required')
 require(public['scripts/friday_ordinary_install.py']==policy['public_helper_sha256']and private['scripts/friday_ordinary_install.py']==policy['private_helper_sha256'],'distinct_private_public_helpers_required')
 newtree=origin_tree(repository,head);origin_blobs(repository,newtree,public);origin_blobs(repository,newtree,policy['reviewed_current_files'],policy['reviewed_current_modes'])
 for name,digest in policy['reviewed_current_files'].items():require(sha(owned(repository/name))==digest,'current_public5_working_drift:'+name)
 for name,digest in private.items():require(sha(owned(C/name))==digest,'current_private503_source_drift:'+name)
 require(origin_git(repository,'rev-parse','HEAD').decode().strip()==head,'current_head_changed_during_origin_check')
 if provenance_mode=='local-committed-main':require(origin_git(repository,'symbolic-ref','-q','HEAD').strip()==b'refs/heads/main'and origin_git(repository,'rev-parse','refs/heads/main').decode().strip()==head,'local_main_changed_during_origin_check')
 return dict(schema='frw.root211.raw-git-full-counterpart-origin-proof.v1',policy=dict(source_binding_refs(acceptance)['origin_policy']),published_snapshot=old['published_snapshot'],completed205_source_commit=policy['completed205_source_commit'],completed206_source_commit=policy['completed206_source_commit'],completed207_source_commit=policy['completed207_source_commit'],completed208_source_commit=policy['completed208_source_commit'],completed209_source_commit=policy['completed209_source_commit'],completed210_source_commit=policy['completed210_source_commit'],current_head=head,fresh_origin_main=fresh_origin,provenance_mode=provenance_mode,remote_publication='DEFERRED_NOT_VERIFIED'if provenance_mode=='local-committed-main'else'FRESH_REMOTE_MAIN_VERIFIED',ancestor_public_files=489,predecessor205_public_files=491,predecessor206_public_files=493,predecessor_public_files=501,public_project_files=503,private_difference_count=28,reviewed_current_file_count=5,target_input_sha256=CURRENT211_INPUT['sha256'],expected_NOT_INSTALLED_receipt_sha256=EXPECTED_RECEIPT)

def validate_snapshot_origin(acceptance,snapshot):
 require(acceptance['source_provenance']=={'mode':snapshot['provenance_mode'],'commit':snapshot['head']},'accepted211_source_provenance_required')
 require(acceptance['public_main_sha']==snapshot['origin_main'],'accepted211_publication_observation_required')
 proof=source_origin(snapshot['head'],snapshot['origin_main'],provenance_mode=snapshot['provenance_mode'],acceptance=acceptance)
 require(snapshot['source_origin']==proof,'exact211_current_origin_proof_required')
 return proof


def validate_predecessor_record(record):
 require(record['schema']=='frw.root.actual210-predecessor.v1'and record['state']=='ROOT_RECONCILED_GENUINE_INSTALLED210_NOT_EXPECTATION'and record['template_only_no_execution_grant']is False,'genuine_actual210_record_required')
 require(all(record[k]==v for k,v in HISTORICAL210_REFS.items()),'exact_completed210_refs_required')
 for value in HISTORICAL210_REFS.values():readref(value)
 closure=readref(record['complete_closure']);request=readref(record['request']);committed=readref(record['committed']);stage=readref(record['source_receipt']);journal=readref(record['root_journal']);ret=readref(record['root_return'])
 require(closure['state']=='INSTALLED210_PROJECT501_NATIVE17891_SERVICES_HEALTHY_OPERATION_CLOSED'and closure['installed']==dict(base=17730,layers=210,native=17891,plugins=52,project=501),'actual210_complete_closure_required')
 require(closure['actors_boundary_publisher_closed']is True and closure['canonical_CP210']==record['request']and closure['root_journal']==record['root_journal']and closure['root_return']==record['root_return'],'actual210_closed_joins_required')
 require(request['schema']=='friday.ordinary-telegram-source-update.v46'and request['installed_layers']==209 and request['home']==str(H)and request['current_input']==ORIGINAL210_INPUT,'actual210_current_input_required')
 require(request['current_source_successor']==dict(schema='friday.current-source-native-successor.v12',root_project_update=ROOT198,previous_native_update=record['actual209_predecessor']),'actual210_ordered_root198_chain_required')
 # Root's just-closed exact210 full consumer has already authenticated198+199..210.
 # Reuse that frozen closure; the ordinary actual210 builder/preflight revalidates current chain.
 require(closure['actual209_predecessor']==record['actual209_predecessor']and closure['full_readback_fresh_default_spec_inspect']is True,'actual210_accepted_chain_and_default_consumer_required')
 require(committed['state']=='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED'and committed['request_reference']==record['request']and committed['request_sha256']==record['request']['sha256']and committed['current_source_successor']==request['current_source_successor']and committed['current_input']==ORIGINAL210_INPUT and committed['source_receipt_sha256']==BEFORE_RECEIPT and committed['gateway_started']is False and committed['workers_enabled']is False,'actual210_committed_stage_required')
 require((len(stage['layers']),len(stage['files']),stage['source_file_count'])==(210,17891,17730),'exact210_stage_inventory_required')
 for key in ('marker','source_receipt','stamp'):require(record[key]['sha256']==closure['canonical4'][key]['sha256'],'actual210_stage_closure_hash_required')
 require(closure['canonical4']['input']==ORIGINAL210_INPUT,'actual210_input_closure_required')
 require(journal['state']=='NATIVE210_PROJECT501_FRESH_PERMANENT_SERVICES_RUNNING'and journal['expected_receipt_sha256']==BEFORE_RECEIPT and journal['native_before_after']==[209,210]and journal['request']['sha256']==record['request']['sha256'],'actual210_Root_journal_required')
 require(journal['full_selected_native_files_readback']and journal['fresh_default_spec_inspect']and journal['user_db_wal_shm_verified_before_starts']and journal['publisher_closed_before_parent_custody_release'],'actual210_readback_closure_required')
 require(ret['returncode']==0 and ret['boundary_pid_absent']is True,'actual210_boundary_closed_required')
 require(not os.path.lexists(Path(record['request']['path']).parent/'rolled-back.json'),'actual210_not_rolled_back_required')
 readref(ROOT198)
 return record['request']

def clean_reference(ref):
 return {k:ref[k]for k in ('path','sha256')}

def actual_predecessor():
 return validate_predecessor_record(readref(reference(B/'ROOT-ACTUAL210-PREDECESSOR.json')))

def validate_project_binding(acceptance=None):
 acceptance=readref(reference(B/'ROOT-211-SOURCE-ACCEPTANCE.json'))if acceptance is None else acceptance
 refs=source_binding_refs(acceptance);record=readref(refs['project_source_proof']);policy=origin_policy(acceptance)
 require(record['schema']=='friday.root.future211.project-source.v1'and record['state']=='ROOT_ACCEPTED_PRIVATE503_PUBLIC5_CONNECTED_NOT_INSTALLED_NOT_GRANTED','exact_Root_accepted503_source_proof_required')
 require(record['template_only_no_execution_grant']is False and record['runtime_grant']is False and record['actual_request_or_UUID_or_admission_created']is False and record['native211_installed']is False,'source_proof_not_runtime_grant')
 require(record['private_project']==str(C)and record['current_input']==CURRENT211_INPUT and record['previous_input']==ORIGINAL210_INPUT,'exact_actual_private503_domain_required')
 actual=readref(record['current_input']);previous=readref(record['previous_input']);prospective=readref(FIXED['prospective_private_input'])
 require(actual==prospective and {k:v for k,v in actual.items()if k!='project_files'}=={k:v for k,v in previous.items()if k!='project_files'},'source211_must_derive_from_actual210_nonproject_fields')
 origins=readref(FIXED['project_origins'])['rows'];require(len(origins)==503 and {n:r['sha256']for n,r in origins.items()}==actual['project_files'],'full503_private_origins_required')
 for name,row in origins.items():require(reference(row['path'])==clean_reference(row)and sha(owned(C/name))==row['sha256'],'actual_private503_source_drift:'+name)
 public=readref(policy['current_public_input']);spec=readref(FIXED['native_spec']);diff=sorted(n for n in actual['project_files']if actual['project_files'][n]!=public['project_files'][n])
 require(set(public['project_files'])==set(actual['project_files'])and len(diff)==spec['private_difference_count']==28 and diff==spec['private_difference_names']==record['private_public28'],'exact_private_public28_required')
 require(record['all503_origin_hashes_verified']is True and record['project_files']==503 and record['installed210_canonical4_unchanged']is True,'Root_source_checks_required')
 require({k:r['sha256']for k,r in record['public_source_changes'].items()}==PUBLIC5,'Root_source_public5_exact_required')
 require(record['source_integration_acceptance']==acceptance['source_integration_acceptance']and readref(record['source_integration_acceptance'])and record['origin_policy']==refs['origin_policy']and record['source_commit']==policy['source_commit'],'Root_source_acceptance_origin_join_required')
 return record

def project_source_pins(request,acceptance=None):
 validate_project_binding(acceptance)
 previous=readref(request['previous_input']);current=readref(request['current_input'])
 require(request['previous_input']['sha256']==PREVIOUS_INPUT,'real_source210_input_required')
 require((len(previous['project_files']),len(current['project_files']))==(501,503),'project501_to503_required')
 for root,value in [(P,previous),(C,current)]:
  for name,digest in value['project_files'].items():require(sha(owned(root/name))==digest,'project_inventory_changed:'+name)
 require({k:v for k,v in previous.items()if k!='project_files'}=={k:v for k,v in current.items()if k!='project_files'},'actual210_nonproject_fields_unchanged_required')
 added=set(current['project_files'])-set(previous['project_files']);changed={n for n in previous['project_files']if previous['project_files'][n]!=current['project_files'].get(n)}
 require(added=={'patches/hermes/r02-telegram-text-uncertain-recovery-after-source210-manifest.json','patches/hermes/r02-telegram-text-uncertain-recovery-after-source210.patch'} and changed=={'scripts/friday_ordinary_install.py'} and not set(previous['project_files'])-set(current['project_files']),'exact_helper_pair_delta_required')
 require(request['project_file_updates']==['scripts/friday_ordinary_install.py'],'exact_private_helper_update_required')
 require(request['plugin_set']==request['plugin_additions']==request['staged_files']==[],'no_plugin_or_worker_staging_required')
 require(request['project_inventory']==current['project_files'],'request_inventory_changed')
 require(request['project_inventory_sha256']==hashlib.sha256(encoded(current['project_files'])).hexdigest(),'inventory_digest_changed')
 require(request['current_input']==request['candidate_input'],'candidate_input_changed')
 return previous,current

def native_after_path(name):
 require(name in {row['path']for row in readref(FIXED['native_spec'])['native_files']},'exact_final211_native_path_required')
 return S/'native-after'/name

def project_receipt(before,spec,current):
 result=copy.deepcopy(before)
 result['layers'].append({'manifest':spec['manifest_rel'],'manifest_sha256':spec['manifest']['sha256'],'patch_sha256':spec['patch']['sha256']})
 lock=current['sources_lock'];result['sources_lock_sha256']=lock['sha256'] if isinstance(lock,dict) else sha(lock)
 for row in spec['native_files']:
  value=dict(result['files'].get(row['path'],{}));value.update(sha256=row['sha256'],bytes=row['bytes'],mode='100644');result['files'][row['path']]=value
 return result

def validate_source_request(request,acceptance=None):
 require(set(request)==set(('schema seconds home candidate_project layer_names marker source_receipt stamp configuration profile launcher native_unit previous_input current_input predecessor_request predecessor_current_input_sha256 predecessor_receipt_sha256 target_receipt candidate_input project_inventory project_inventory_sha256 plugin_set plugin_additions project_file_updates staged_files layer_manifest_updates installed_layers installed_files transaction_history current_source_successor').split()),'exact_builder_fields_no_test_injection_required')
 canonical={'marker':H/'FRIDAY-INSTALL.json','source_receipt':H/'hermes-agent.source.json','target_receipt':H/'hermes-agent.source.json','stamp':H/'hermes-agent/install-stamp.json','configuration':H/'config.yaml','profile':H/'FRIDAY-PROFILE.json','launcher':H/'hermes-agent/.hermes/bin/hermes','native_unit':Path('/home/jericho/.config/systemd/user/hermes-gateway-1b7e7667.service'),'previous_input':S210/'INPUT-SOURCE210.PROSPECTIVE.NOT_INSTALLED.json','current_input':S/'INPUT-SOURCE211.PROSPECTIVE.NOT_INSTALLED.json','candidate_input':S/'INPUT-SOURCE211.PROSPECTIVE.NOT_INSTALLED.json','predecessor_request':H/'preparation/ordinary-source-update-successor-afb9863d58ee319d96e00e313a8cc495c6cb883f75430e7adcbb24c80ef5de00/request.json'}
 require(all(request[key]['path']==str(path) for key,path in canonical.items()),'canonical_request_paths_required')
 require(request['current_input']=={'path':str(S/'INPUT-SOURCE211.PROSPECTIVE.NOT_INSTALLED.json'),'sha256':CURRENT211_INPUT['sha256']},'exact_final211_input_required')
 require(request['previous_input']=={'path':str(S210/'INPUT-SOURCE210.PROSPECTIVE.NOT_INSTALLED.json'),'sha256':PREVIOUS_INPUT},'exact_final211_input_required')
 require(request['target_receipt']==request['source_receipt'],'one_current_receipt_required')
 require(request['predecessor_request']['sha256']=='afb9863d58ee319d96e00e313a8cc495c6cb883f75430e7adcbb24c80ef5de00' and request['predecessor_current_input_sha256']=='3948650d65fa78b48aa3bc838d4948815af2b75e4db5fffe29886c2707c7f93c' and request['predecessor_receipt_sha256']=='2c0eea5c2647172a0d059c2993c898b401c7d808bbcc85ee766d51aae7c0e51d','genuine_historical_root_predecessor_required')
 require(request['schema']=='friday.ordinary-telegram-source-update.v46','explicit_v46_required')
 require(request['home']==str(H) and request['candidate_project']==str(C),'exact_home_candidate_required')
 require(request['seconds']==600 and type(request['seconds']) is int,'forward600_required')
 require(request['layer_names']==[LAYER],'one_explicit_eleventh_layer_required')
 require(request['installed_layers']==210 and request['installed_files']==17891,'true210_required')
 require(request['current_source_successor']=={'schema':'friday.current-source-native-successor.v13','root_project_update':ROOT198,'previous_native_update':actual_predecessor()},'genuine_root198_to210_chain_required')
 readref(ROOT198);readref(actual_predecessor())
 for key in ('marker','source_receipt','stamp','configuration','profile','launcher','native_unit','previous_input','current_input','predecessor_request','target_receipt','candidate_input'):
  # Some runtime pins (launcher/config/unit) are not JSON; only verify bytes/identity.
  ref=request[key];require(reference(ref['path'])==ref,'request_pin_changed:'+key)
 require(request['source_receipt']['sha256']==BEFORE_RECEIPT,'genuine_current210_receipt_required')
 previous,current=project_source_pins(request,acceptance)
 spec=readref(FIXED['native_spec']);before=readref(request['source_receipt'])
 require((len(before['layers']),len(before['files']),before['source_file_count'])==(210,17891,17730),'real210_inventory_required')
 require(len(spec['native_files'])==4 and sum(row['new_file'] for row in spec['native_files'])==0,'four_existing_paths_no_native_absent_required')
 require({row['path']for row in spec['native_files']}=={'gateway/delivery_ledger.py', 'gateway/run_startup.py', 'plugins/platforms/telegram/adapter.py', 'gateway/platforms/base.py'},'exact_four_final211_paths_required')
 require(request['layer_manifest_updates']==[spec['manifest_rel']],'only_new_pair_required')
 for row in spec['native_files']:
  path=H/'hermes-agent'/row['path']
  require(not os.path.lexists(path) if row['new_file'] else reference(path)['sha256']==row['before_sha256'],'native_preimage_changed:'+row['path'])
  require(sha(owned(native_after_path(row['path'])))==row['sha256'],'native_afterimage_changed:'+row['path'])
 for role in ['manifest','patch']:require(reference(spec[role]['path'])=={k:spec[role][k] for k in ('path','sha256')},'pair_changed')
 projected=project_receipt(before,spec,current)
 require((len(projected['layers']),len(projected['files']))==(211,17891),'projection_count_wrong')
 expected=readref(FIXED['prospective_composition'])
 require(projected==expected['expected_inventory'] and hashlib.sha256(encoded(projected)).hexdigest()==EXPECTED_RECEIPT,'exact211_projection_required')
 require(projected['layers'][:-1]==before['layers'],'exact210_prefix_required')
 native_paths={row['path'] for row in spec['native_files']}
 untouched={name:row for name,row in before['files'].items() if name not in native_paths}
 require(len(untouched)==17887 and {name:row for name,row in projected['files'].items() if name not in native_paths}==untouched,'all17887_untouched_native_rows_required')
 targets={str(H/'hermes-agent'/row['path']):{'before_sha256':row['before_sha256'],'after_sha256':row['sha256'],'native_new':row['new_file']} for row in spec['native_files']}
 for name in request['project_file_updates']+[spec['manifest_rel'],spec['patch_rel']]:
  path=H/name;targets[str(path)]={'before_sha256':previous['project_files'].get(name),'after_sha256':current['project_files'][name],'native_new':False}
 for key in ['marker','source_receipt','stamp']:targets[request[key]['path']]={'before_sha256':request[key]['sha256'],'metadata':True}
 require(len(targets)==10,'exact_ten_targets_required')
 for path,pin in targets.items():
  require(not os.path.lexists(path) if pin['before_sha256'] is None else reference(path)['sha256']==pin['before_sha256'],'selected_target_preimage_changed:'+path)
 return {'expected_receipt_sha256':hashlib.sha256(encoded(projected)).hexdigest(),'selected_target_count':10,'selected_targets':targets,'before_layers':210,'after_layers':211,'native_files_after':17891,'project_files_after':503,'current_input':request['current_input'],'previous_input':request['previous_input'],'native_spec':FIXED['native_spec']}

def validate_independent_acceptances(acceptance):
 for key,scope in [('independent_actual_bulk_acceptance','actual-bulk'),('independent_frame_acceptance','frame')]:
  record=readref(acceptance[key])
  require(record['schema']=='frw.root.native211.independent-source-acceptance.v1'and record['scope']==scope,'independent211_acceptance_scope_required')
  require(record['approved']is True and record['accepted']is True and record['source_only']is True and record['execution_grant']is False and record['installed211_or_runtime_accepted']is False and record['template_only_no_execution_grant']is False,'independent211_source_acceptance_not_runtime_required')
  require(record['review_evidence'],'independent211_actual_review_evidence_required')
  for ref in record['review_evidence']:readref(ref)
  if scope=='actual-bulk':
   require(record['source_bindings']=={name:FIXED[name]for name in ('source_result','source_freeze','native_spec','prospective_private_input','prospective_public_input')},'independent211_exact_bulk_bindings_required')
  else:
   require(record['frame_source_manifest']==acceptance['frame_source_manifest']==reference(B/'SOURCE-PINS.json'),'independent211_exact_frame_bindings_required')

def validate_join(request,acceptance,snapshot,*,now,boot_id):
 for ref in FIXED.values():readref(ref)
 require(acceptance['schema']=='frw.root.native211-source-acceptance.v1'and acceptance['state']=='ROOT_ACCEPTED_EXACT211_R02_SOURCE_OFFLINE_NOT_RUNTIME','root_source_acceptance_required')
 require(acceptance['accepted']is True and acceptance['execution_grant']is False and acceptance['template_only_no_execution_grant']is False,'source_acceptance_only')
 require(acceptance['source_pins']==FIXED,'exact_prepared_source_pins_required')
 require(acceptance['final_source_result']==FIXED['source_result']and readref(acceptance['source_integration_acceptance']),'exact211_f07_source_acceptance_required')
 require(acceptance['r02_source_evidence']=={key:FIXED[key]for key in ('composition_journal_checks','metadata_consumer_checks','final_readback','independent_source_review')},'exact211_source_evidence_required')
 require(acceptance['source_only_evidence_accepted']is True and acceptance['fresh_from_base_private_graph_qualified']is False and acceptance['broader_log_privacy_accepted']is False and acceptance['r02_semantic_or_formal_accepted']is False,'source_only_limits_required')
 source=readref(FIXED['source_result'])
 require(source['state']=='SOURCE_ONLY_FINAL_TRUE210_TO211_V13_COHORT_REVIEWED_UNBOUND_NOT_INSTALLED'and source['grants']['installation']is False and source['native_modifications']==4 and source['selected_targets']==10,'exact211_existing_source_results_required')
 require(acceptance['v13_whole_transaction_and_default_postconsumer_precondition']=='NOT_RUN_POSTCONDITION_OF_SAME_ADMITTED_TRANSACTION','future_default_result_must_not_be_precondition')
 require(acceptance['frame_source_manifest']==reference(B/'SOURCE-PINS.json')and acceptance['frame_review_evidence'],'new_coherent_frame_review_required')
 for ref in acceptance['frame_review_evidence']+acceptance['independent_review_evidence']:readref(ref)
 require(acceptance['independent_review_evidence'],'actual_independent_review_required')
 validate_independent_acceptances(acceptance)
 result=validate_source_request(request,acceptance)
 require(snapshot['schema']=='frw.root.native211-fresh-readback.v1'and snapshot['state']=='ROOT_CURRENT_READBACK_NOT_EXECUTION_GRANT','fresh_root_readback_required')
 require(snapshot['template_only_no_execution_grant']is False,'actual_readback_not_template_required')
 require(snapshot['boot_id']==boot_id,'current_boot_required');fresh(snapshot['observed_at_moscow'],now,'fresh_readback_required')
 require(all(snapshot['checks'][key]is True for key in SNAPSHOT_TRUE_FIELDS),'all_current_boundary_checks_required')
 origin_proof=validate_snapshot_origin(acceptance,snapshot)
 require(len(snapshot['head'])==40 and all(c in '0123456789abcdef'for c in snapshot['head']),'real_git_sha_required')
 require(snapshot['installed_receipt_sha256']==BEFORE_RECEIPT and snapshot['installed_input_sha256']==PREVIOUS_INPUT,'current_source210_pins_required')
 for service in ('gateway','dashboard'):
  identity=snapshot['services'][service];require(identity['boot_id']==boot_id and type(identity['pid'])is int and identity['pid']>0 and type(identity['birth_ticks'])is int and identity['birth_ticks']>0,'fresh_process_identity_required')
  require(len(identity['invocation_id'])==32 and identity['cgroup'].startswith('/user.slice/')and identity['enabled_active']is True and identity['runtime_max']=='infinity','healthy_permanent_service_required')
 require(snapshot['evidence'],'fresh_actual_readback_evidence_required')
 for ref in snapshot['evidence']:readref(ref)
 require(snapshot['remaining_limits']=={'native_canonical_unknown':3,'structural_unresolved':45,'R104_semantic_fail':True,'default_workers_ready_accepted':False,'DSH_A0_deferred':True},'known_limits_must_remain')
 require(snapshot['unexposed_all_profile_pending_queues_proved']is False,'unexposed_queue_limit_must_remain')
 result.update(source_origin=origin_proof,genuine_actual210_predecessor=actual_predecessor(),fresh_root_services=copy.deepcopy(snapshot['services']),state='PURE_METADATA_BOUND_NOT_ADMISSION',source_acceptance={'path':str(B/'ROOT-211-SOURCE-ACCEPTANCE.json'),'sha256':hashlib.sha256(encoded(acceptance)).hexdigest()},snapshot_boot_id=boot_id,operation_seconds=1800,forward_seconds=600,external_rollback_seconds=180,publisher_terminal_cleanup_seconds=30,publisher_unit_seconds=810,publisher_client_seconds=840)
 return result

def validate_profile_join(qualification,before,spec):
 require(qualification['schema']=='frw.root.native211-minimum-installed-bank-profile-qualification.v1','profile211_schema_required')
 require(qualification['template_only_no_execution_grant']is False and qualification['source_before_after']==[210,211],'actual211_profile_revalidation_required')
 require(qualification['profile_equivalence_join']==PROFILE_SOURCE_JOIN,'exact_reviewed_unchanged_profile_join_required')
 join=readref(PROFILE_SOURCE_JOIN)
 old={name:before['files'][name]['sha256']for name in ('hermes_cli/friday_workspace_pdf.py','hermes_cli/friday_workspace_presentation.py')}
 require(not set(old)&{row['path']for row in spec['native_files']},'f07_211_must_not_change_bank_profile_files')
 require(join['state']=='SOURCE_ONLY_EXACT206_PROFILE_UNCHANGED_IN207_NO_NEW_APP_CREDIT'and join['before_profile_source_digests']==join['after_profile_source_digests']==old and qualification['before_profile_source_digests']==qualification['minimum_profile_source_digests']==old,'exact210_unchanged211_profile_required')
 require(join['changed_profile_definitions']==[]and join['new_Office_effects']==0 and join['saved_app_evidence_reused']is True,'no_new_Office_credit')
 for source in join['evidence']:readref(source)
 require(qualification['format_layout_ready']is False and qualification['formal_test_credit']is False,'no_new_layout_formal_credit')
 return old

def load_actor_binding(bundle):
 require(Path(bundle).resolve()==B,'exact_bundle_required')
 request=readref(reference(B/'ROOT-FRESH-REQUEST.json'));acceptance=readref(reference(B/'ROOT-211-SOURCE-ACCEPTANCE.json'))
 snapshot=readref(reference(B/'ROOT-211-FRESH-READBACK.json'))
 value=validate_join(request,acceptance,snapshot,now=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 saved=readref(reference(B/'ROOT-211-BOUND-INPUTS.json'))
 require(saved['binding']==value,'bound_input_join_changed')
 for key in ['request','source_acceptance','fresh_readback']:
  name={'request':'ROOT-FRESH-REQUEST.json','source_acceptance':'ROOT-211-SOURCE-ACCEPTANCE.json','fresh_readback':'ROOT-211-FRESH-READBACK.json'}[key]
  require(saved[key]==reference(B/name),'saved_input_ref_changed')
 return value

def main():
 p=argparse.ArgumentParser();p.add_argument('--validate-and-bind',action='store_true',required=True);args=p.parse_args()
 require(__debug__ and sys_flags_safe(),'isolated_nonoptimized_no_bytecode_required')
 request=readref(reference(B/'ROOT-FRESH-REQUEST.json'));acceptance=readref(reference(B/'ROOT-211-SOURCE-ACCEPTANCE.json'));snapshot=readref(reference(B/'ROOT-211-FRESH-READBACK.json'))
 value=validate_join(request,acceptance,snapshot,now=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 payload={'binding':value,**{key:reference(B/name) for key,name in [('request','ROOT-FRESH-REQUEST.json'),('source_acceptance','ROOT-211-SOURCE-ACCEPTANCE.json'),('fresh_readback','ROOT-211-FRESH-READBACK.json')]}}
 destination=B/'ROOT-211-BOUND-INPUTS.json';fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as stream:stream.write(encoded(payload));stream.flush();os.fsync(stream.fileno())
 print(json.dumps({'state':value['state'],'bound_inputs':reference(destination),'execution_grant':False}))
def sys_flags_safe():
 import sys
 return bool(sys.flags.isolated and sys.dont_write_bytecode)
if __name__=='__main__':main()
