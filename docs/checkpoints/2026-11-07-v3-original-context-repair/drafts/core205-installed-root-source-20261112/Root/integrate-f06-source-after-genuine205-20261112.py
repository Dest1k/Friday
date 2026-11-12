"""Root exact source integration only, after genuine205. No runtime install."""
from pathlib import Path
import datetime,hashlib,json,os,stat,subprocess
B=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
S=Path('/home/jericho/.cache/FRW-SOL-V3-F06-NORMAL-SUCCESSOR-SOURCE-20261112')
D=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE493-SOURCE-20261112')
R=Path('/home/jericho/jericho/Friday_rework');H=R/'.runtime/friday-normal-both-workers-frw032'
OUT=B/'F06-PUBLIC5-ACTUAL205-SOURCE-INTEGRATION-20261112'
os.umask(0o077)
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def save(p,v):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as o:o.write((json.dumps(v,sort_keys=True,indent=2)+'\n').encode());o.flush();os.fsync(o.fileno())
def main():
 proof=load(B/'CORE205-ACTUAL-INSTALLED-CLOSED-20261112.json')
 assert sha(B/'CORE205-ACTUAL-INSTALLED-CLOSED-20261112.json')=='b26122f9b99ae6c906da802f34420c9d6205ca1319e9f74e5ffe46a246f2b910'
 assert proof['state']=='INSTALLED205_PROJECT491_NATIVE17891_SERVICES_HEALTHY_OPERATION_CLOSED'
 assert ref(proof['operation']['path'])==proof['operation']and ref(proof['canonical_CP205']['path'])==proof['canonical_CP205']and ref(proof['committed']['path'])==proof['committed']
 for row in proof['installed']['canonical4'].values():assert ref(row['path'])==row
 previous=load(proof['installed']['canonical4']['current_input']['path'])
 assert len(previous['project_files'])==491
 actual205_operation=load(proof['operation']['path']);selected205=Path(actual205_operation['selected_project'])
 assert selected205==Path(load(proof['canonical_CP205']['path'])['candidate_project'])
 for path,digest in actual205_operation['restore_verified_inputs']['settled_files'].items():assert sha(path)==digest
 prefix=[]
 for name,digest in sorted(previous['project_files'].items()):
  p=selected205/name;info=p.lstat();assert stat.S_ISREG(info.st_mode)and info.st_uid==os.getuid()and info.st_nlink==1 and not any(x.is_symlink()for x in(p,*p.parents))and sha(p)==digest
  prefix.append([name,digest])
 assert sha(S/'RESULT.json')=='64fe5b5688db6b711b0204e1bd4db9100c28d21881574f047b2789f7a2d5c107'
 assert sha(S/'SOURCE-FREEZE.json')=='f1be05ce4e5b6a047d9ef90b465eec38b884ed08e9febe8234a797b4924872e0'
 for row in load(S/'SOURCE-FREEZE.json')['rows']:assert sha(row['path'])==row['sha256']
 rootstand=load(D/'RESULT.json');assert sha(D/'RESULT.json')=='5dd08dcc0a576fbd8edd2ab3d35aab30e948d6271ccf6ad79a44478aa04fbe8f'
 assert len(rootstand['rows'])==493
 for name,row in rootstand['rows'].items():
  p=D/'project493'/name;info=p.lstat();assert stat.S_ISREG(info.st_mode)and info.st_nlink==1 and not any(x.is_symlink()for x in(p,*p.parents))and sha(p)==row['sha256']
 prospective=load(S/'INPUT-SOURCE206.PROSPECTIVE.NOT_INSTALLED.json')
 assert {k:v for k,v in previous.items()if k!='project_files'}=={k:v for k,v in prospective.items()if k!='project_files'}
 actual=dict(previous);actual['project_files']={name:row['sha256']for name,row in rootstand['rows'].items()}
 assert actual==prospective
 spec=load(S/'FINAL-NATIVE-SPEC.json');assert len(spec['native_files'])==11
 for row in spec['native_files']:assert row['new_file']is False and sha(H/'hermes-agent'/row['path'])==row['before_sha256']
 recipe=load(S/'ROOT-INTEGRATION-RECIPE-PREPARED.json');public=recipe['exact_future_public5']
 assert len(public)==5 and sha(S/'PUBLIC-INTEGRATION.patch')=='0685a59a00266e5d30ca60189ca5df079eec8662e7674a3f36c327b35302fd13'
 for row in public.values():assert sha(row['path'])==row['sha256']
 # Verify original helper and all three modified source preimages through exact patch.
 subprocess.run(['git','-C',str(R),'--no-optional-locks','apply','--check',str(S/'PUBLIC-INTEGRATION.patch')],check=True)
 OUT.mkdir(mode=0o700)
 before={}
 for name in public:
  p=R/name
  if p.exists():
   before[name]=ref(p);dest=OUT/'before'/name;dest.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
   fd=os.open(dest,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
   with os.fdopen(fd,'wb')as o:o.write(p.read_bytes())
  else:before[name]=None
 save(OUT/'INTENT.json',dict(state='FUTURE206_PUBLIC_SOURCE_ONLY_NOT_INSTALLED',at_moscow=datetime.datetime.now().astimezone().isoformat(),actual205=ref(B/'CORE205-ACTUAL-INSTALLED-CLOSED-20261112.json'),before=before,after=public))
 save(D/'INPUT-SOURCE206.json',actual)
 assert sha(D/'INPUT-SOURCE206.json')=='e6e480448509b336824b1aa13f27c359cc89eb4612c0317eb6a877cdb9586e39'
 subprocess.run(['git','-C',str(R),'--no-optional-locks','apply','--whitespace=nowarn',str(S/'PUBLIC-INTEGRATION.patch')],check=True)
 for name,row in public.items():assert sha(R/name)==row['sha256']
 result=dict(schema='frw.root.f06.public-source-after-genuine205.v1',state='EXACT_FUTURE206_PUBLIC5_CONNECTED_NOT_INSTALLED',at_moscow=datetime.datetime.now().astimezone().isoformat(),
  actual205=ref(B/'CORE205-ACTUAL-INSTALLED-CLOSED-20261112.json'),canonical_CP205=proof['canonical_CP205'],actual205_nonproject_fields_preserved=True,
  all491_actual205_selected_source_preimages_verified=True,actual205_selected_installed_H_targets_verified=True,selected205_project=str(selected205),project_preimage_digest=hashlib.sha256(json.dumps(prefix,separators=(',',':')).encode()).hexdigest(),
  input206=ref(D/'INPUT-SOURCE206.json'),candidate_project=str(D/'project493'),public5=public,before=before,native11_preimages_verified=True,
  no_H_write_or_service_or_Office_model_user_effect=True,next='Commit exact source/proofs; prepare coherent206 Root frame with genuineCP205, current provenance and normal explicit layer. Actual206 request/UUID/admission still absent.',
  public_private_differences=28,full_V3_closed=False)
 save(OUT/'RESULT.json',result);print(json.dumps(dict(state=result['state'],proof=ref(OUT/'RESULT.json'),input206=result['input206'])))
if __name__=='__main__':main()
