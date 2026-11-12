"""Use Root's existing protected495 sourceproof directly; never duplicate bindings."""
from pathlib import Path
import ast,hashlib,json,os,re
B=Path(__file__).parent;assert not(B/'SOURCE-PINS.json').exists();os.umask(0o077)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def raw(v):return(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def put(n,v):
 p=B/n;p.write_bytes(v.encode()if isinstance(v,str)else raw(v));p.chmod(0o600)
def load(n):return json.loads((B/n).read_bytes())
proof=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE495-SOURCE-20261112/ROOT-207-PROJECT-SOURCE.json');assert sha(proof)=='1b83332bd3e0c44aebffd0114fe6bdc3d87ee8894dae4c90cdce1fd2584a8ba5'
source="""def validate_project_binding():
 # Root materialized this sourceproof, independently of future request/runtimeauthority.
 record=readref(PROJECT_SOURCE_PROOF)
 require(record['schema']=='friday.root.future207.project-source.v1'and record['state']=='ROOT_MATERIALIZED_PRIVATE495_PUBLIC5_CONNECTED_NOT_INSTALLED_NOT_GRANTED','exact_Root_materialized495_source_proof_required')
 require(record['runtime_grant']is False and record['actual_request_or_UUID_or_admission_created']is False and record['native207_installed']is False,'source_proof_not_runtime_grant')
 require(record['private_project']==str(C)and record['current_input']=={'path':str(S/'INPUT-SOURCE207.json'),'sha256':'c7a01f639606652f75db11418b5abd6e3a03b0babea09627570e39b0865ff838'}and record['previous_input']==ORIGINAL206_INPUT,'exact_actual_private495_domain_required')
 actual=readref(record['current_input']);previous=readref(record['previous_input']);policy=readref(ORIGIN_POLICY);prospective=readref(policy['prospective_private_input'])
 require(actual==prospective and {k:v for k,v in actual.items()if k!='project_files'}=={k:v for k,v in previous.items()if k!='project_files'},'actual207_must_derive_from_actual206_nonproject_fields')
 origins=readref(FIXED['project_origins'])['rows'];require(len(origins)==495 and {n:r['sha256']for n,r in origins.items()}==actual['project_files'],'full495_private_origins_required')
 for name,row in origins.items():require(reference(row['path'])=={k:row[k]for k in ('path','sha256')}and sha(owned(C/name))==row['sha256'],'actual_private495_source_drift:'+name)
 public=readref(policy['current_public_input']);counterpart=readref(FIXED['counterparts']);diff=sorted(n for n in actual['project_files']if actual['project_files'][n]!=public['project_files'][n])
 require(set(public['project_files'])==set(actual['project_files'])and len(diff)==counterpart['private_difference_count']==28 and diff==counterpart['private_difference_names']==record['private_public28'],'exact_private_public28_required')
 require(record['all495_origin_hashes_verified']is True and record['project_files']==495 and record['installed206_canonical4_unchanged']is True,'Root_materialization_checks_required')
 require({k:r['sha256']for k,r in record['public_source_changes'].items()}==policy['reviewed_current_files'],'Root_source_public5_exact_required')
 return record
"""
p=B/'root207_metadata.py';s=p.read_text();n=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)and n.name=='validate_project_binding');lines=s.splitlines(keepends=True);s=''.join(lines[:n.lineno-1])+source+''.join(lines[n.end_lineno:]);s=s.replace('ORIGINAL206_INPUT=',"PROJECT_SOURCE_PROOF="+repr(dict(path=str(proof),sha256=sha(proof)))+"\nORIGINAL206_INPUT=",1);put(p.name,s)
# The former UNBOUND private495 adapter never existed. Root's one source proof is sufficient.
template=B/'ROOT-207-PROJECT-SOURCE-TEMPLATE.json';put('PROJECT-SOURCE-ADAPTER-SUPERSESSION.json',dict(old_unused_template_sha256=sha(template),actual_binding_created=False,replacement=dict(path=str(proof),sha256=sha(proof)),reason='Reuse Root existing exact495proof; freshly validate bytes/28origins at consumer boundary, no duplicate source binding.'));template.unlink()
s=(B/'run_native207_once.py').read_text();s,n=re.subn(r"assert sha\(B / 'root207_metadata.py'\) == '[0-9a-f]{64}'","assert sha(B / 'root207_metadata.py') == '"+sha(p)+"'",s);assert n==1;put('run_native207_once.py',s)
v=load('ROOT-207-FRESH-ADMISSION-TEMPLATE.json');v['actor']=dict(path=str(B/'run_native207_once.py'),sha256=sha(B/'run_native207_once.py'));put('ROOT-207-FRESH-ADMISSION-TEMPLATE.json',v)
# Update only affected pureconsumer fixture; preserve original82-observation as beforechange evidence.
c=B/'source_controls.py';s=c.read_text();s=s.replace("binding=load(B/'ROOT-207-PROJECT-SOURCE-TEMPLATE.json');binding.update(state='ROOT_MATERIALIZED_EXACT_PRIVATE495_FROM_ACTUAL206',template_only_no_execution_grant=False,physical495_verified=True,private_public28_verified=True)","binding=load(m.PROJECT_SOURCE_PROOF['path'])")
s=s.replace("str(B/'ROOT-207-PROJECT-SOURCE.json'):binding","m.PROJECT_SOURCE_PROOF['path']:binding").replace("str(B/'ROOT-207-PROJECT-SOURCE.json')","m.PROJECT_SOURCE_PROOF['path']")
s=s.replace("('wrong_public_input',lambda r:r.update(actual_input=policy['current_public_input']))","('wrong_public_input',lambda r:r.update(current_input=policy['current_public_input']))").replace("('wrong_project_domain',lambda r:r.update(actual_project='/synthetic/wrong'))","('wrong_project_domain',lambda r:r.update(private_project='/synthetic/wrong'))").replace("('physical_not_verified',lambda r:r.update(physical495_verified=False))","('physical_not_verified',lambda r:r.update(all495_origin_hashes_verified=False))").replace("('counterpart_not_verified',lambda r:r.update(private_public28_verified=False))","('counterpart_not_verified',lambda r:r.update(private_public28=[]))")
# Project sourceproof remains externally pinned; virtual mutations emulate a substituted reference
# to exercise semantic checks, while exactdigest check is exercised separately below.
s=s.replace("if ref['path']in virtual_json:\n  m.require(vref(ref['path'])==ref,'virtual_reference_hash_changed');return", "if ref['path']in virtual_json:\n  m.require(vref(ref['path'])==ref or ref==m.PROJECT_SOURCE_PROOF,'virtual_reference_hash_changed');return")
s=s.replace("check('actual_project_binding_function_virtual495_positive'", "check('Root_materialized_sourceproof_consumer_virtual495_positive'")
put('source_controls.py',s)
p=B/'SOURCE-CONTROLS.json';p.rename(B/'SOURCE-CONTROLS-BEFORE-ROOT-SOURCE-PROOF-ADAPTER.json')
print(json.dumps(dict(state='ADAPTED_EXACT_ROOT495_SOURCE_PROOF_NOT_RUNTIME',sourceproof_sha256=sha(proof))))
