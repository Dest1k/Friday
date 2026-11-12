"""Pure metadata observer/join for a later Root-owned genuine207 to208 boundary.
Import performs no product read, collector, consumer call, request or grant. The optional
CLI can only exclusively write its own bound metadata after Root supplies actual files.
Source/projection, historical closure, current observations and fresh authority are distinct.
"""
from pathlib import Path
import argparse,copy,datetime,hashlib,json,os,stat,time
B=Path(__file__).resolve().parent
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
S=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112')
S207=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE495-SOURCE-20261112')
F207=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT207-ROOT-SOURCE-AFTER206-20261112')
P=S207/'project495'
C=S/'project497'
LAYER='inbound-turn-log-metadata-after-source207'
BEFORE_RECEIPT='faf5d6ad698b7250b09545508352c120c0c8cdf653cecb9c37afeb2601c98a4b'
PREVIOUS_INPUT='c7a01f639606652f75db11418b5abd6e3a03b0babea09627570e39b0865ff838'
EXPECTED_RECEIPT='7b69cfdfb61962dc26986800bcd47a3bbce1884c39e9418f42b2febeec5dd750'
ROOT198={'path': '/home/jericho/.cache/FRW-ASTRA-V3-DSH-COHERENT-ROOT-COMPOSITION-20261111/final-v1/fresh-source-request/REQUEST.json', 'sha256': '886c6ab5bc76a810b24004f7042ef7c1b5add1b78f04781fac9c96335e3bd448'}
# Immutable source evidence and closed207 history; none conveys a fresh runtime grant.
FIXED={'native_spec': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112/FINAL-NATIVE-SPEC.json', 'sha256': 'f09987fe57e3138e04160c74ba679c817e6f74313f210e867234c011a6f422ed'}, 'source_freeze': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112/SOURCE-FREEZE.json', 'sha256': '7a83355124341feef19c4843de0cebf85b84352152f6f6be6aef867cef7774b8'}, 'prospective_composition': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112/NATIVE208-PROSPECTIVE-COMPOSITION.json', 'sha256': '2a3cda6d04e155aa791629e5606eb98132dc195c92e8047bbc957c6843c54717'}, 'project_origins': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112/PROJECT497-ORIGINS.json', 'sha256': '5a8b3890b58200d42a2eea46b339b3529410f38274f12dcf9ed0071f598b377f'}, 'public_origins': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112/PUBLIC497-ORIGINS.json', 'sha256': '382e24c943ec2ef9c0abce09a2f289091da4b139501533e5950b3405bd25541d'}, 'actual207_provenance': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112/ACTUAL207-PROVENANCE.json', 'sha256': '46137efd3cd666850bfcedd0252775d54c8d59674ac9369f0bd6694d57287aa4'}, 'prospective_private_input': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112/INPUT-SOURCE208.PROSPECTIVE.NOT_INSTALLED.json', 'sha256': '37f63d76bc9b09d5109bc6387aaf160f351be93878e4c1d1495ab066f0a85a24'}, 'prospective_public_input': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112/INPUT-SOURCE208.PUBLIC.PROSPECTIVE.NOT_INSTALLED.json', 'sha256': '83a174939935d1991f786ecb9b055e168394f2db646f6cf43328e5cc029a811d'}, 'all_history_limit': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112/ALL-HISTORY-PROBE-OBSERVATION.json', 'sha256': '3c084e9f2e914aa7c3dd4c79fcfdd1990ed800b66c1e9c8fe41dac12039481a3'}, 'actual_builder_preflight': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112/ACTUAL-BUILDER-CONSUMER-CHECK.json', 'sha256': 'df18e7ead615362da6048d7224eb4eb6eaadf1bf9e5d79df7425b28dd0aae220'}, 'source_result': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112/postpower-20261113/RESULT.json', 'sha256': '7452163fb5abc79fbbe6c2217e0d27e822be84d5efcb45c3113d0c5dc555c7e6'}, 'prepared_root_recipe': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112/postpower-20261113/ROOT-NEXT-RECIPE.json', 'sha256': 'f7be9e556de82642184661a8295c4acac7b1c7a457f4339a5e169937c053158b'}, 'finalrefs': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112/postpower-20261113/FINALREFS.json', 'sha256': 'c63cf9bdca710960b6d7e6c6d556ed5ed718088a87282f524772b12e76c66b8b'}, 'residualchecks': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112/postpower-20261113/RESIDUALCHECKS.json', 'sha256': '282d6dafdf010d313252069dff0e3a2bf3ca1750ae981abed5090b61b34472dc'}, 'pin_reconciliation': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112/postpower-20261113/pin-reconciliation/RESULT.json', 'sha256': '1552979aeedb418af5f8d540b87707502e417c4c6315677b0025a56150848a36'}, 'actual207_closure': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/CORE207-ACTUAL-INSTALLED-CLOSED-20261112.json', 'sha256': '996b43c584c8eb6d5c8dbbeb60f500958c873427cda0881ae74a7618d920f963'}, 'root_source_integration_acceptance': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-CORE208-ROOT-20261113/ROOT-SOURCE-INTEGRATION-ACCEPTANCE.json', 'sha256': '42b71df6d61d9e5e27b3302eff9592edcb3cac4c839eef1260d931e1af7b81a4'}, 'pm_environment_basis': {'path': '/home/jericho/.cache/FRW-SOL-V3-CORE204-RTF-READER-COMPOSITION-20261111/READONLY-PM-ENVIRONMENT-BASIS.json', 'sha256': '2ab5df26d6bd153ccc175e5813ad0fd769be377611b653fee486e3c3fab2062e'}}
ORIGINAL207_INPUT={'path':str(S207/'INPUT-SOURCE207.json'),'sha256':PREVIOUS_INPUT}
CURRENT208_INPUT=dict(FIXED['prospective_private_input'])
ORIGINAL207_ORIGIN_POLICY={'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT207-ROOT-SOURCE-AFTER206-20261112/ROOT-207-PUBLIC-ORIGIN-POLICY.json', 'sha256': 'f8d29ef77b72a0de92010b8b013c88a662a5a6c9f3663312209d6382750bc548'}
PROFILE_SOURCE_JOIN={'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT207-ROOT-SOURCE-AFTER206-20261112/PROFILE-SOURCE-JOIN.json', 'sha256': '9d1c1e6fdaadc68f07eba2425007071cc14bae4c80af203f9b37d54587e53746'}
COMPLETED207_SOURCE_COMMIT='fddb0abc70ea9d1caed3dbd5186a0a0b52166e46'
PUBLIC5={'docs/checkpoints/2026-11-07-v3-original-context-repair/build-layer-publication-request.py': '2ea5c42b8f8e5143709082c4db78de3ce864447dd499a6140a7435a1e8f07bdd', 'docs/checkpoints/2026-11-07-v3-original-context-repair/friday_v3_layer_publication.py': '291f84d171dbc98b5710b2fd2aebea76bd26105f06d7a3f9961e3592dff83d97', 'patches/hermes/inbound-turn-log-metadata-after-source207-manifest.json': '742d2a1b8f3de54e647ee17a607910480bac49685026173c9c368236b03b4db4', 'patches/hermes/inbound-turn-log-metadata-after-source207.patch': '2045aa2d0603a63c0cc5eeb72fbb4bdaab907d18ee521e6b383cf0948f851f7f', 'scripts/friday_ordinary_install.py': '6384d98892dd5c180f8a2e00cddfc31dc2cf2c872f4dd1f6739dcf808f06d645'}
PUBLIC5_MODES={name:('100755'if name.endswith('/friday_v3_layer_publication.py')else'100644')for name in PUBLIC5}
HISTORICAL207_REFS={'request': {'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/preparation/ordinary-source-update-v45-6320a882b34740a5/request.json', 'sha256': '6320a882b34740a5e76b876ce3531a1966e58a9d2ebaf00162e684226042c89c'}, 'committed': {'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/preparation/ordinary-source-update-v45-6320a882b34740a5/committed.json', 'sha256': '3c58a7d2b1c012a16ff5208d438d8e88c5c74123a2d88ad9d0fb9c26f8466b4f'}, 'intent': {'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/preparation/ordinary-source-update-v45-6320a882b34740a5/intent.json', 'sha256': 'a3756b972c93810445af29e6b08061646739a8227bfa5042015dcfcade1c5c21'}, 'source_receipt': {'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/preparation/ordinary-source-update-v45-6320a882b34740a5/hermes-agent.source.json', 'sha256': 'faf5d6ad698b7250b09545508352c120c0c8cdf653cecb9c37afeb2601c98a4b'}, 'marker': {'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/preparation/ordinary-source-update-v45-6320a882b34740a5/FRIDAY-INSTALL.json', 'sha256': '91e8f0747c551e90a9637e9ed44fb0af1c8933dfdd5edee67cd531cd9c5ee7bb'}, 'stamp': {'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/preparation/ordinary-source-update-v45-6320a882b34740a5/install-stamp.json', 'sha256': 'e224d0ffa894426c5322826cd35e41aac77ffce1d89dc1c16d4eeeb4cd529ee0'}, 'complete_closure': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/CORE207-ACTUAL-INSTALLED-CLOSED-20261112.json', 'sha256': '996b43c584c8eb6d5c8dbbeb60f500958c873427cda0881ae74a7618d920f963'}, 'root_journal': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT207-ROOT-SOURCE-AFTER206-20261112/ROOT-NATIVE207-LIVE-OPERATION.json', 'sha256': '91eb36de3a60bcd456ab7c7a6c4884c08f1bfcfb686aed212f7c98ce3b7f8a22'}, 'root_return': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT207-ROOT-SOURCE-AFTER206-20261112/FUTURE-EXECUTION/RETURN.json', 'sha256': '11d3a35323c2ae3506987e1be54e64905507fa7f39efb95f75ca98335758ad0e'}}
SNAPSHOT_TRUE_FIELDS=(
 'source_authority_verified','public_source_pins_verified','operational_source_pins_verified',
 'profile_routing_verified','process_environment_verified','ordinary_readonly_quiescent',
 'all_three_user_db_zero_leases','stop_cooldown_clear','sole_heavy_slot_clear',
 'no_current_maintenance','cancellation_clear','resources_sufficient',
 'all_profile_owned_work_quiescent','current_request_unconsumed','old_effects_not_replayed',
 'native_pm_selected_python_verified','product_services_healthy_infinite_lifetime',
 'unchanged_bank_profile_evidence_reusable','known_limits_retained')
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
 acceptance=readref(reference(B/'ROOT-208-SOURCE-ACCEPTANCE.json'))if acceptance is None else acceptance
 require(type(acceptance)is dict,'Root_source_acceptance_object_required')
 refs={name:acceptance[name]for name in ('origin_policy','project_source_proof')}
 require(refs['origin_policy']['path']==str(B/'ROOT-208-PUBLIC-ORIGIN-POLICY.json')and refs['project_source_proof']['path']==str(B/'ROOT-208-PROJECT-SOURCE.json'),'own_Root_source_binding_paths_required')
 return refs

def origin_policy(acceptance=None):
 acceptance=readref(reference(B/'ROOT-208-SOURCE-ACCEPTANCE.json'))if acceptance is None else acceptance
 refs=source_binding_refs(acceptance);policy=readref(refs['origin_policy'])
 old=readref(ORIGINAL207_ORIGIN_POLICY)
 require(policy['schema']=='frw.root208.raw-git-full-counterpart-origin-policy.v1'and policy['execution_grant']is False and policy['template_only_no_execution_grant']is False,'actual_Root208_source_origin_policy_required')
 require(policy['predecessor207_origin_policy']==ORIGINAL207_ORIGIN_POLICY and policy['completed207_source_commit']==COMPLETED207_SOURCE_COMMIT,'exact_completed207_source_origin_required')
 for key in ('published_ancestor48_policy','completed205_public_input','completed205_source_commit','completed206_public_input','completed206_source_commit'):
  require(policy[key]==old[key],'unchanged_ancestral_origin_policy_required:'+key)
 require(policy['completed207_public_input']==old['current_public_input'],'exact_completed207_public495_required')
 require(policy['current_private_project']==str(C)and policy['expected_actual_input']==CURRENT208_INPUT and policy['previous_input']==ORIGINAL207_INPUT,'exact208_private_source_domain_required')
 require(policy['current_public_input']==FIXED['prospective_public_input']and policy['private_origins']==FIXED['project_origins']and policy['public_origins']==FIXED['public_origins'],'exact208_source_origins_required')
 require(policy['reviewed_current_files']==PUBLIC5 and policy['reviewed_current_modes']==PUBLIC5_MODES,'exact208_public5_policy_required')
 require(policy['source_commit']==acceptance['source_provenance']['commit'],'exact208_Root_commit_policy_join_required')
 require(policy['public_helper_sha256']==PUBLIC5['scripts/friday_ordinary_install.py']and policy['private_helper_sha256']=='11f085babcbb8184f78236ebdffe56e238d261d91333e27686163710605bbc25','exact208_distinct_helpers_required')
 require(policy['expected208_receipt_sha256']==EXPECTED_RECEIPT,'projection_only_receipt_pin_required')
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
 for commit in [head,old['published_snapshot'],policy['completed205_source_commit'],policy['completed206_source_commit'],policy['completed207_source_commit']]:
  require(git_oid('commit',origin_git(repository,'cat-file','commit',commit))==commit,'raw_commit_identity_changed');origin_git(repository,'merge-base','--is-ancestor',commit,head)
 ancestor=readref(old['public_input'])['project_files'];require(len(ancestor)==489,'exact48public489_required')
 oldtree=origin_tree(repository,old['published_snapshot']);origin_blobs(repository,oldtree,ancestor);origin_blobs(repository,oldtree,old['snapshot_guards'],old['snapshot_guard_modes'])
 for name,row in old['retained_executed_sources'].items():require(reference(row['path'])=={k:row[k]for k in ('path','sha256')}and row['sha256']==old['snapshot_guards'][name],'old48_executed_source_join_changed')
 for number,count in [(205,491),(206,493),(207,495)]:
  prior=readref(policy['completed'+str(number)+'_public_input'])['project_files'];require(len(prior)==count,'exact_predecessor_public_inventory_required');origin_blobs(repository,origin_tree(repository,policy['completed'+str(number)+'_source_commit']),prior)
 public=readref(policy['current_public_input'])['project_files'];private=readref(CURRENT208_INPUT)['project_files'];spec=readref(FIXED['native_spec'])
 require(set(public)==set(private)and len(public)==497,'exact208public_private497_required')
 differences=sorted(name for name in public if public[name]!=private[name])
 require(differences==spec['private_difference_names']and len(differences)==spec['private_difference_count']==28,'exact28_private_public_differences_required')
 require(public['scripts/friday_ordinary_install.py']==policy['public_helper_sha256']and private['scripts/friday_ordinary_install.py']==policy['private_helper_sha256'],'distinct_private_public_helpers_required')
 newtree=origin_tree(repository,head);origin_blobs(repository,newtree,public);origin_blobs(repository,newtree,policy['reviewed_current_files'],policy['reviewed_current_modes'])
 for name,digest in policy['reviewed_current_files'].items():require(sha(owned(repository/name))==digest,'current_public5_working_drift:'+name)
 for name,digest in private.items():require(sha(owned(C/name))==digest,'current_private497_source_drift:'+name)
 require(origin_git(repository,'rev-parse','HEAD').decode().strip()==head,'current_head_changed_during_origin_check')
 if provenance_mode=='local-committed-main':require(origin_git(repository,'symbolic-ref','-q','HEAD').strip()==b'refs/heads/main'and origin_git(repository,'rev-parse','refs/heads/main').decode().strip()==head,'local_main_changed_during_origin_check')
 return dict(schema='frw.root208.raw-git-full-counterpart-origin-proof.v1',policy=dict(source_binding_refs(acceptance)['origin_policy']),published_snapshot=old['published_snapshot'],completed205_source_commit=policy['completed205_source_commit'],completed206_source_commit=policy['completed206_source_commit'],completed207_source_commit=policy['completed207_source_commit'],current_head=head,fresh_origin_main=fresh_origin,provenance_mode=provenance_mode,remote_publication='DEFERRED_NOT_VERIFIED'if provenance_mode=='local-committed-main'else'FRESH_REMOTE_MAIN_VERIFIED',ancestor_public_files=489,predecessor205_public_files=491,predecessor206_public_files=493,predecessor_public_files=495,public_project_files=497,private_difference_count=28,reviewed_current_file_count=5,target_input_sha256=CURRENT208_INPUT['sha256'],expected_NOT_INSTALLED_receipt_sha256=EXPECTED_RECEIPT)

def validate_snapshot_origin(acceptance,snapshot):
 require(acceptance['source_provenance']=={'mode':snapshot['provenance_mode'],'commit':snapshot['head']},'accepted208_source_provenance_required')
 require(acceptance['public_main_sha']==snapshot['origin_main'],'accepted208_publication_observation_required')
 proof=source_origin(snapshot['head'],snapshot['origin_main'],provenance_mode=snapshot['provenance_mode'],acceptance=acceptance)
 require(snapshot['source_origin']==proof,'exact208_current_origin_proof_required')
 return proof

def validate_predecessor_record(record):
 require(record['schema']=='frw.root.actual207-predecessor.v1'and record['state']=='ROOT_RECONCILED_GENUINE_INSTALLED207_NOT_EXPECTATION'and record['template_only_no_execution_grant']is False,'genuine_actual207_record_required')
 require(all(record[k]==v for k,v in HISTORICAL207_REFS.items()),'exact_completed207_refs_required')
 for ref in HISTORICAL207_REFS.values():readref(ref)
 historical=readref(FIXED['actual207_provenance']);closure=readref(record['complete_closure'])
 require(closure['state']=='INSTALLED207_PROJECT495_NATIVE17891_SERVICES_HEALTHY_OPERATION_CLOSED'and closure['operation']==record['root_journal']and closure['canonical_CP207']==record['request']and closure['actors_and_boundary_closed']is True,'actual207_completed_closure_required')
 stage_receipt=readref(record['source_receipt'])
 require((len(stage_receipt['layers']),len(stage_receipt['files']),stage_receipt['source_file_count'])==(207,17891,17730),'exact_completed207_inventory_required')
 chain=historical['canonical_chain']
 require(len(chain)==9 and [row['schema']for row in chain]==['friday.current-source-native-successor.v'+str(n)for n in range(1,10)]and clean_reference(historical['canonical_native207_request'])==record['request'],'exact199_to207_nine_edge_chain_required')
 for index,row in enumerate(chain):
  req=readref(clean_reference(row['request']));committed=readref(clean_reference(row['committed']));stage=readref(clean_reference(row['stage_metadata']['hermes-agent.source.json']));readref(clean_reference(row['intent']));n=199+index
  tx=H/'preparation'/('ordinary-source-update-v45-'+row['request']['sha256'][:16])
  require(row['request']['path']==str(tx/'request.json')and row['committed']['path']==str(tx/'committed.json')and row['intent']['path']==str(tx/'intent.json')and row['stage_metadata']['hermes-agent.source.json']['path']==str(tx/'hermes-agent.source.json'),'canonical_chain_paths_required')
  require(req['home']==str(H)and req['schema']=='friday.ordinary-telegram-source-update.v46'and req['installed_layers']==n-1 and len(req['layer_names'])==1,'exact_historical_edge_required')
  successor=req['current_source_successor'];require(successor['schema']==row['schema']and successor['root_project_update']==row['root_project_update']==ROOT198,'exact_historical_version_root198_required')
  require(successor.get('previous_native_update')==(clean_reference(chain[index-1]['request'])if index else None),'exact_ordered_previous_native_chain_required')
  require(req['current_input']==row['current_input']and req['previous_input']==row['previous_input'],'exact_chain_input_join_required')
  require(committed['state']=='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED'and committed['request_reference']==clean_reference(row['request'])and committed['request_sha256']==row['request']['sha256']and committed['source_receipt_sha256']==row['stage_metadata']['hermes-agent.source.json']['sha256']and committed['current_input']==req['current_input']and committed['current_source_successor']==successor and committed['gateway_started']is False and committed['workers_enabled']is False,'genuine_committed_chain_stage_required')
  require(stage['layers']==stage_receipt['layers'][:n],'complete_stage_prefix_required')
  require(not os.path.lexists(tx/'rolled-back.json'),'committed_stage_not_rollback_required')
 request=readref(record['request']);committed=readref(record['committed'])
 require(request['current_input']==ORIGINAL207_INPUT and committed['source_receipt_sha256']==BEFORE_RECEIPT and closure['installed']['canonical4']['current_input']==ORIGINAL207_INPUT,'actual207_input_receipt_join_required')
 require(closure['installed']==dict(base=17730,layers=207,native=17891,plugins=52,project=495,canonical4=closure['installed']['canonical4']),'actual207_full_counts_required')
 journal=readref(record['root_journal']);require(journal['state']=='NATIVE207_PROJECT495_FRESH_PERMANENT_SERVICES_RUNNING'and journal['expected_receipt_sha256']==BEFORE_RECEIPT and journal['native_before_after']==[206,207],'actual207_Root_journal_required')
 require(journal['request']['sha256']==record['request']['sha256']and readref(journal['request'])==request,'actual207_Root_canonical_request_join_required')
 require(journal['full_selected_native_files_readback']and journal['fresh_default_spec_inspect']and journal['user_db_wal_shm_verified_before_starts']and journal['publisher_closed_before_parent_custody_release'],'actual207_fresh_consumer_and_closure_required')
 ret=readref(record['root_return']);require(ret['returncode']==0 and ret['boundary_pid_absent']is True,'actual207_boundary_closed_required')
 readref(ROOT198)
 return record['request']

def clean_reference(ref):
 return {k:ref[k]for k in ('path','sha256')}

def actual_predecessor():
 return validate_predecessor_record(readref(reference(B/'ROOT-ACTUAL207-PREDECESSOR.json')))

def validate_project_binding(acceptance=None):
 refs=source_binding_refs(acceptance);record=readref(refs['project_source_proof']);policy=origin_policy(acceptance)
 require(record['schema']=='friday.root.future208.project-source.v1'and record['state']=='ROOT_ACCEPTED_PRIVATE497_PUBLIC5_CONNECTED_NOT_INSTALLED_NOT_GRANTED','exact_Root_accepted497_source_proof_required')
 require(record['template_only_no_execution_grant']is False and record['runtime_grant']is False and record['actual_request_or_UUID_or_admission_created']is False and record['native208_installed']is False,'source_proof_not_runtime_grant')
 require(record['private_project']==str(C)and record['current_input']==CURRENT208_INPUT and record['previous_input']==ORIGINAL207_INPUT,'exact_actual_private497_domain_required')
 actual=readref(record['current_input']);previous=readref(record['previous_input']);prospective=readref(FIXED['prospective_private_input'])
 require(actual==prospective and {k:v for k,v in actual.items()if k!='project_files'}=={k:v for k,v in previous.items()if k!='project_files'},'source208_must_derive_from_actual207_nonproject_fields')
 origins=readref(FIXED['project_origins'])['rows'];require(len(origins)==497 and {n:r['sha256']for n,r in origins.items()}==actual['project_files'],'full497_private_origins_required')
 for name,row in origins.items():require(reference(row['path'])==clean_reference(row)and sha(owned(C/name))==row['sha256'],'actual_private497_source_drift:'+name)
 public=readref(policy['current_public_input']);spec=readref(FIXED['native_spec']);diff=sorted(n for n in actual['project_files']if actual['project_files'][n]!=public['project_files'][n])
 require(set(public['project_files'])==set(actual['project_files'])and len(diff)==spec['private_difference_count']==28 and diff==spec['private_difference_names']==record['private_public28'],'exact_private_public28_required')
 require(record['all497_origin_hashes_verified']is True and record['project_files']==497 and record['installed207_canonical4_unchanged']is True,'Root_source_checks_required')
 require({k:r['sha256']for k,r in record['public_source_changes'].items()}==PUBLIC5,'Root_source_public5_exact_required')
 require(record['source_integration_acceptance']==FIXED['root_source_integration_acceptance']and record['origin_policy']==refs['origin_policy']and record['source_commit']==policy['source_commit'],'Root_source_acceptance_origin_join_required')
 return record

def project_source_pins(request,acceptance=None):
 validate_project_binding(acceptance)
 previous=readref(request['previous_input']);current=readref(request['current_input'])
 require(request['previous_input']['sha256']==PREVIOUS_INPUT,'real_source207_input_required')
 require((len(previous['project_files']),len(current['project_files']))==(495,497),'project495_to497_required')
 for root,value in [(P,previous),(C,current)]:
  for name,digest in value['project_files'].items():require(sha(owned(root/name))==digest,'project_inventory_changed:'+name)
 require({k:v for k,v in previous.items()if k!='project_files'}=={k:v for k,v in current.items()if k!='project_files'},'actual207_nonproject_fields_unchanged_required')
 added=set(current['project_files'])-set(previous['project_files']);changed={n for n in previous['project_files']if previous['project_files'][n]!=current['project_files'].get(n)}
 require(added=={'patches/hermes/inbound-turn-log-metadata-after-source207-manifest.json','patches/hermes/inbound-turn-log-metadata-after-source207.patch'} and changed=={'scripts/friday_ordinary_install.py'} and not set(previous['project_files'])-set(current['project_files']),'exact_helper_pair_delta_required')
 require(request['project_file_updates']==['scripts/friday_ordinary_install.py'],'exact_private_helper_update_required')
 require(request['plugin_set']==request['plugin_additions']==request['staged_files']==[],'no_plugin_or_worker_staging_required')
 require(request['project_inventory']==current['project_files'],'request_inventory_changed')
 require(request['project_inventory_sha256']==hashlib.sha256(encoded(current['project_files'])).hexdigest(),'inventory_digest_changed')
 require(request['current_input']==request['candidate_input'],'candidate_input_changed')
 return previous,current

def project_receipt(before,spec,current):
 result=copy.deepcopy(before)
 result['layers'].append({'manifest':spec['manifest_rel'],'manifest_sha256':spec['manifest']['sha256'],'patch_sha256':spec['patch']['sha256']})
 lock=current['sources_lock'];result['sources_lock_sha256']=lock['sha256'] if isinstance(lock,dict) else sha(lock)
 for row in spec['native_files']:
  value=dict(result['files'].get(row['path'],{}));value.update(sha256=row['sha256'],bytes=row['bytes'],mode='100644');result['files'][row['path']]=value
 return result

def validate_source_request(request,acceptance=None):
 require(set(request)==set(('schema seconds home candidate_project layer_names marker source_receipt stamp configuration profile launcher native_unit previous_input current_input predecessor_request predecessor_current_input_sha256 predecessor_receipt_sha256 target_receipt candidate_input project_inventory project_inventory_sha256 plugin_set plugin_additions project_file_updates staged_files layer_manifest_updates installed_layers installed_files transaction_history current_source_successor').split()),'exact_builder_fields_no_test_injection_required')
 canonical={'marker':H/'FRIDAY-INSTALL.json','source_receipt':H/'hermes-agent.source.json','target_receipt':H/'hermes-agent.source.json','stamp':H/'hermes-agent/install-stamp.json','configuration':H/'config.yaml','profile':H/'FRIDAY-PROFILE.json','launcher':H/'hermes-agent/.hermes/bin/hermes','native_unit':Path('/home/jericho/.config/systemd/user/hermes-gateway-1b7e7667.service'),'previous_input':S207/'INPUT-SOURCE207.json','current_input':S/'INPUT-SOURCE208.PROSPECTIVE.NOT_INSTALLED.json','candidate_input':S/'INPUT-SOURCE208.PROSPECTIVE.NOT_INSTALLED.json','predecessor_request':H/'preparation/ordinary-source-update-successor-afb9863d58ee319d96e00e313a8cc495c6cb883f75430e7adcbb24c80ef5de00/request.json'}
 require(all(request[key]['path']==str(path) for key,path in canonical.items()),'canonical_request_paths_required')
 require(request['current_input']=={'path':str(S/'INPUT-SOURCE208.PROSPECTIVE.NOT_INSTALLED.json'),'sha256':CURRENT208_INPUT['sha256']},'exact_final208_input_required')
 require(request['previous_input']=={'path':str(S207/'INPUT-SOURCE207.json'),'sha256':PREVIOUS_INPUT},'exact_final208_input_required')
 require(request['target_receipt']==request['source_receipt'],'one_current_receipt_required')
 require(request['predecessor_request']['sha256']=='afb9863d58ee319d96e00e313a8cc495c6cb883f75430e7adcbb24c80ef5de00' and request['predecessor_current_input_sha256']=='3948650d65fa78b48aa3bc838d4948815af2b75e4db5fffe29886c2707c7f93c' and request['predecessor_receipt_sha256']=='2c0eea5c2647172a0d059c2993c898b401c7d808bbcc85ee766d51aae7c0e51d','genuine_historical_root_predecessor_required')
 require(request['schema']=='friday.ordinary-telegram-source-update.v46','explicit_v46_required')
 require(request['home']==str(H) and request['candidate_project']==str(C),'exact_home_candidate_required')
 require(request['seconds']==600 and type(request['seconds']) is int,'forward600_required')
 require(request['layer_names']==[LAYER],'one_explicit_tenth_layer_required')
 require(request['installed_layers']==207 and request['installed_files']==17891,'true207_required')
 require(request['current_source_successor']=={'schema':'friday.current-source-native-successor.v10','root_project_update':ROOT198,'previous_native_update':actual_predecessor()},'genuine_root198_to207_chain_required')
 readref(ROOT198);readref(actual_predecessor())
 for key in ('marker','source_receipt','stamp','configuration','profile','launcher','native_unit','previous_input','current_input','predecessor_request','target_receipt','candidate_input'):
  # Some runtime pins (launcher/config/unit) are not JSON; only verify bytes/identity.
  ref=request[key];require(reference(ref['path'])==ref,'request_pin_changed:'+key)
 require(request['source_receipt']['sha256']==BEFORE_RECEIPT,'genuine_current207_receipt_required')
 previous,current=project_source_pins(request,acceptance)
 spec=readref(FIXED['native_spec']);before=readref(request['source_receipt'])
 require((len(before['layers']),len(before['files']),before['source_file_count'])==(207,17891,17730),'real207_inventory_required')
 require(len(spec['native_files'])==2 and sum(row['new_file'] for row in spec['native_files'])==0,'two_existing_paths_no_native_absent_required')
 require({row['path']for row in spec['native_files']}=={'gateway/run_turn.py','agent/turn_context.py'},'exact_two_native_logging_paths_required')
 require(request['layer_manifest_updates']==[spec['manifest_rel']],'only_new_pair_required')
 for row in spec['native_files']:
  path=H/'hermes-agent'/row['path']
  require(not os.path.lexists(path) if row['new_file'] else reference(path)['sha256']==row['before_sha256'],'native_preimage_changed:'+row['path'])
  require(sha(owned(S/'native-after'/row['path']))==row['sha256'],'native_afterimage_changed:'+row['path'])
 for role in ['manifest','patch']:require(reference(spec[role]['path'])=={k:spec[role][k] for k in ('path','sha256')},'pair_changed')
 projected=project_receipt(before,spec,current)
 require((len(projected['layers']),len(projected['files']))==(208,17891),'projection_count_wrong')
 expected=readref(FIXED['prospective_composition'])
 require(projected==expected['expected_inventory'] and hashlib.sha256(encoded(projected)).hexdigest()==EXPECTED_RECEIPT,'exact208_projection_required')
 require(projected['layers'][:-1]==before['layers'],'exact207_prefix_required')
 native_paths={row['path'] for row in spec['native_files']}
 untouched={name:row for name,row in before['files'].items() if name not in native_paths}
 require(len(untouched)==17889 and {name:row for name,row in projected['files'].items() if name not in native_paths}==untouched,'all17889_untouched_native_rows_required')
 targets={str(H/'hermes-agent'/row['path']):{'before_sha256':row['before_sha256'],'after_sha256':row['sha256'],'native_new':row['new_file']} for row in spec['native_files']}
 for name in request['project_file_updates']+[spec['manifest_rel'],spec['patch_rel']]:
  path=H/name;targets[str(path)]={'before_sha256':previous['project_files'].get(name),'after_sha256':current['project_files'][name],'native_new':False}
 for key in ['marker','source_receipt','stamp']:targets[request[key]['path']]={'before_sha256':request[key]['sha256'],'metadata':True}
 require(len(targets)==8,'exact_eight_targets_required')
 for path,pin in targets.items():
  require(not os.path.lexists(path) if pin['before_sha256'] is None else reference(path)['sha256']==pin['before_sha256'],'selected_target_preimage_changed:'+path)
 return {'expected_receipt_sha256':hashlib.sha256(encoded(projected)).hexdigest(),'selected_target_count':8,'selected_targets':targets,'before_layers':207,'after_layers':208,'native_files_after':17891,'project_files_after':497,'current_input':request['current_input'],'previous_input':request['previous_input'],'native_spec':FIXED['native_spec']}

def validate_independent_acceptances(acceptance):
 for key,scope in [('independent_actual_bulk_acceptance','actual-bulk'),('independent_frame_acceptance','frame')]:
  record=readref(acceptance[key])
  require(record['schema']=='frw.root.native208.independent-source-acceptance.v1'and record['scope']==scope,'independent208_acceptance_scope_required')
  require(record['approved']is True and record['accepted']is True and record['source_only']is True and record['execution_grant']is False and record['installed208_or_runtime_accepted']is False and record['template_only_no_execution_grant']is False,'independent208_source_acceptance_not_runtime_required')
  require(record['review_evidence'],'independent208_actual_review_evidence_required')
  for ref in record['review_evidence']:readref(ref)
  if scope=='actual-bulk':
   require(record['source_bindings']=={name:FIXED[name]for name in ('source_result','finalrefs','native_spec','prospective_private_input','prospective_public_input')},'independent208_exact_bulk_bindings_required')
  else:
   require(record['frame_source_manifest']==acceptance['frame_source_manifest']==reference(B/'SOURCE-PINS.json'),'independent208_exact_frame_bindings_required')

def validate_join(request,acceptance,snapshot,*,now,boot_id):
 for ref in FIXED.values():readref(ref)
 require(acceptance['schema']=='frw.root.native208-source-acceptance.v1'and acceptance['state']=='ROOT_ACCEPTED_EXACT208_LOGGING_SOURCE_OFFLINE_NOT_RUNTIME','root_source_acceptance_required')
 require(acceptance['accepted']is True and acceptance['execution_grant']is False and acceptance['template_only_no_execution_grant']is False,'source_acceptance_only')
 require(acceptance['source_pins']==FIXED,'exact_prepared_source_pins_required')
 require(acceptance['final_source_result']==FIXED['source_result']and acceptance['source_integration_acceptance']==FIXED['root_source_integration_acceptance'],'exact208_logging_source_acceptance_required')
 require(acceptance['logging_source_evidence']=={key:FIXED[key]for key in ('finalrefs','residualchecks','pin_reconciliation','actual_builder_preflight','all_history_limit')},'exact208_source_evidence_required')
 require(acceptance['source_only_evidence_accepted']is True and acceptance['power_interrupted_original_preserved']is True and acceptance['fresh_from_base_private_graph_qualified']is False and acceptance['broader_log_privacy_accepted']is False,'source_only_limits_required')
 residual=readref(FIXED['residualchecks'])
 require(residual['state']=='PASS_MISSING_WHOLE_SUCCESS_AND_LATE_DEFAULT_ROLLBACK_SOURCE_ONLY'and [row['kind']for row in residual['fresh_runs']]==['operational-success','operational-rollback']and residual['powerlossatomicity_claim']is False,'exact208_source_fixture_results_required')
 for row in residual['fresh_runs']:
  readref(clean_reference(row['execution']));readref(clean_reference(row['report']))
  require(row['authority']=='EXPLICIT_SYNTHETIC_SOURCE_ONLY_NOT_ACTUAL_ADMISSION_OR_PRODUCT_ACCEPTANCE'and row['pid_absent']is True and row['temporary_fixture_removed']is True,'source_fixtures_not_actual_authority')
 require(acceptance['frame_source_manifest']==reference(B/'SOURCE-PINS.json')and acceptance['frame_review_evidence'],'new_coherent_frame_review_required')
 for ref in acceptance['frame_review_evidence']+acceptance['independent_review_evidence']:readref(ref)
 require(acceptance['independent_review_evidence'],'actual_independent_review_required')
 validate_independent_acceptances(acceptance)
 result=validate_source_request(request,acceptance)
 require(snapshot['schema']=='frw.root.native208-fresh-readback.v1'and snapshot['state']=='ROOT_CURRENT_READBACK_NOT_EXECUTION_GRANT','fresh_root_readback_required')
 require(snapshot['template_only_no_execution_grant']is False,'actual_readback_not_template_required')
 require(snapshot['boot_id']==boot_id,'current_boot_required');fresh(snapshot['observed_at_moscow'],now,'fresh_readback_required')
 require(all(snapshot['checks'][key]is True for key in SNAPSHOT_TRUE_FIELDS),'all_current_boundary_checks_required')
 origin_proof=validate_snapshot_origin(acceptance,snapshot)
 require(len(snapshot['head'])==40 and all(c in '0123456789abcdef'for c in snapshot['head']),'real_git_sha_required')
 require(snapshot['installed_receipt_sha256']==BEFORE_RECEIPT and snapshot['installed_input_sha256']==PREVIOUS_INPUT,'current_source207_pins_required')
 for service in ('gateway','dashboard'):
  identity=snapshot['services'][service];require(identity['boot_id']==boot_id and type(identity['pid'])is int and identity['pid']>0 and type(identity['birth_ticks'])is int and identity['birth_ticks']>0,'fresh_process_identity_required')
  require(len(identity['invocation_id'])==32 and identity['cgroup'].startswith('/user.slice/')and identity['enabled_active']is True and identity['runtime_max']=='infinity','healthy_permanent_service_required')
 require(snapshot['evidence'],'fresh_actual_readback_evidence_required')
 for ref in snapshot['evidence']:readref(ref)
 require(snapshot['remaining_limits']=={'native_canonical_unknown':3,'structural_unresolved':45,'R104_semantic_fail':True,'default_workers_ready_accepted':False,'DSH_A0_deferred':True},'known_limits_must_remain')
 require(snapshot['unexposed_all_profile_pending_queues_proved']is False,'unexposed_queue_limit_must_remain')
 result.update(source_origin=origin_proof,genuine_actual207_predecessor=actual_predecessor(),fresh_root_services=copy.deepcopy(snapshot['services']),state='PURE_METADATA_BOUND_NOT_ADMISSION',source_acceptance={'path':str(B/'ROOT-208-SOURCE-ACCEPTANCE.json'),'sha256':hashlib.sha256(encoded(acceptance)).hexdigest()},snapshot_boot_id=boot_id,operation_seconds=1800,forward_seconds=600,external_rollback_seconds=180,publisher_terminal_cleanup_seconds=30,publisher_unit_seconds=810,publisher_client_seconds=840)
 return result

def validate_profile_join(qualification,before,spec):
 require(qualification['schema']=='frw.root.native208-minimum-installed-bank-profile-qualification.v1','profile208_schema_required')
 require(qualification['template_only_no_execution_grant']is False and qualification['source_before_after']==[207,208],'actual208_profile_revalidation_required')
 require(qualification['profile_equivalence_join']==PROFILE_SOURCE_JOIN,'exact_reviewed_unchanged_profile_join_required')
 join=readref(PROFILE_SOURCE_JOIN)
 old={name:before['files'][name]['sha256']for name in ('hermes_cli/friday_workspace_pdf.py','hermes_cli/friday_workspace_presentation.py')}
 require(not set(old)&{row['path']for row in spec['native_files']},'logging208_must_not_change_bank_profile_files')
 require(join['state']=='SOURCE_ONLY_EXACT206_PROFILE_UNCHANGED_IN207_NO_NEW_APP_CREDIT'and join['before_profile_source_digests']==join['after_profile_source_digests']==old and qualification['before_profile_source_digests']==qualification['minimum_profile_source_digests']==old,'exact207_unchanged208_profile_required')
 require(join['changed_profile_definitions']==[]and join['new_Office_effects']==0 and join['saved_app_evidence_reused']is True,'no_new_Office_credit')
 for source in join['evidence']:readref(source)
 require(qualification['format_layout_ready']is False and qualification['formal_test_credit']is False,'no_new_layout_formal_credit')
 return old

def load_actor_binding(bundle):
 require(Path(bundle).resolve()==B,'exact_bundle_required')
 request=readref(reference(B/'ROOT-FRESH-REQUEST.json'));acceptance=readref(reference(B/'ROOT-208-SOURCE-ACCEPTANCE.json'))
 snapshot=readref(reference(B/'ROOT-208-FRESH-READBACK.json'))
 value=validate_join(request,acceptance,snapshot,now=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 saved=readref(reference(B/'ROOT-208-BOUND-INPUTS.json'))
 require(saved['binding']==value,'bound_input_join_changed')
 for key in ['request','source_acceptance','fresh_readback']:
  name={'request':'ROOT-FRESH-REQUEST.json','source_acceptance':'ROOT-208-SOURCE-ACCEPTANCE.json','fresh_readback':'ROOT-208-FRESH-READBACK.json'}[key]
  require(saved[key]==reference(B/name),'saved_input_ref_changed')
 return value

def main():
 p=argparse.ArgumentParser();p.add_argument('--validate-and-bind',action='store_true',required=True);args=p.parse_args()
 require(__debug__ and sys_flags_safe(),'isolated_nonoptimized_no_bytecode_required')
 request=readref(reference(B/'ROOT-FRESH-REQUEST.json'));acceptance=readref(reference(B/'ROOT-208-SOURCE-ACCEPTANCE.json'));snapshot=readref(reference(B/'ROOT-208-FRESH-READBACK.json'))
 value=validate_join(request,acceptance,snapshot,now=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 payload={'binding':value,**{key:reference(B/name) for key,name in [('request','ROOT-FRESH-REQUEST.json'),('source_acceptance','ROOT-208-SOURCE-ACCEPTANCE.json'),('fresh_readback','ROOT-208-FRESH-READBACK.json')]}}
 destination=B/'ROOT-208-BOUND-INPUTS.json';fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as stream:stream.write(encoded(payload));stream.flush();os.fsync(stream.fileno())
 print(json.dumps({'state':value['state'],'bound_inputs':reference(destination),'execution_grant':False}))
def sys_flags_safe():
 import sys
 return bool(sys.flags.isolated and sys.dont_write_bytecode)
if __name__=='__main__':main()
