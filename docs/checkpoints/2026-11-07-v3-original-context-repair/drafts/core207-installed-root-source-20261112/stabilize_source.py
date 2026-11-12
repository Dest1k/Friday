"""Explicit pre-freeze nearest-consumer fixes and accepted dependency pins. Source only."""
from pathlib import Path
import hashlib,json,os,re
B=Path(__file__).parent
assert not(B/'SOURCE-PINS.json').exists()
os.umask(0o077)
def raw(v):return(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def load(n):return json.loads((B/n).read_bytes())
def put(n,v):
 p=B/n;p.write_bytes(v.encode()if isinstance(v,str)else raw(v));p.chmod(0o600)
def edits(n,changes):
 s=(B/n).read_text()
 for a,b in changes.items():assert a in s,(n,a);s=s.replace(a,b)
 put(n,s)
edits('root207_metadata.py',{'ORIGINAL205_INPUT':'ORIGINAL206_INPUT',"closure['canonical_CP205']":"closure['canonical_CP206']","journal['native_before_after']==[204,206]":"journal['native_before_after']==[205,206]",'genuine_actual205_predecessor=':'genuine_actual206_predecessor='})
edits('boundary_contract.py',{'actual205_predecessor=':'actual206_predecessor='})
edits('f06-207-first-actual-root.py',{'# Old native203 rows are historical; current205 is proven separately.':'# Old native203 rows are historical; current206 is proven separately.'})
review=ref('/home/jericho/.cache/FRW-ASTRA-REVIEW-F06-MODERN207-ACTUAL-GATES-20261112/RESULT.json');assert review['sha256']=='b72a443369ae611db4e339b05c6a6a9a0d1c6ce018d923565b0413a93017f42e'
accepted=ref('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/F06-MODERN207-FINAL-EXECUTION-ROOT-ACCEPTANCE-20261112.json');assert accepted['sha256']=='c73c762908b563efafd6f49c7652f3f7ef0f2be2cb9f89964eb6763c0bc23c33'
v=load('REUSED-207-FINAL-SOURCE-EVIDENCE.json');v.update(state='EXACT_MODERN207_SOURCE_FOUR_SYNTHETIC_GATES_INDEPENDENTLY_REVIEWED_ROOT_ACCEPTED_SOURCE_ONLY_NOT_LIVE_GRANT',final_execution_review=review,root_final_execution_acceptance=accepted);put('REUSED-207-FINAL-SOURCE-EVIDENCE.json',v)
s=(B/'root207_metadata.py').read_text();s=s.replace("review=acceptance['modern_final_execution_review'];require(review!=reused['source_gateprep_review']", "review=acceptance['modern_final_execution_review'];require(review==reused['final_execution_review'] and review!=reused['source_gateprep_review']")
s=s.replace("readref(reused['root_source_gate_authorization']);", "readref(reused['root_final_execution_acceptance']);readref(reused['root_source_gate_authorization']);")
put('root207_metadata.py',s)
v=load('ROOT-207-SOURCE-ACCEPTANCE-TEMPLATE.json');v.update(modern_final_execution_review=review,independent_review_evidence=[v['independent_review_evidence'][0],review],known_limits='Exact modern207source/fouractualsyntheticgates reviewed b72a44/Rootsourceaccepted c73c76; notlivegrant. New frame review, Root actual495/input/HEAD/mode/currentanchor/authority remain UNBOUND. Modern7 originalFAIL/editnone and alloldunclosedlimits unchanged. SourceR3privacy separate. No powerlossatomicity.');put('ROOT-207-SOURCE-ACCEPTANCE-TEMPLATE.json',v)
s=(B/'run_native207_once.py').read_text();s,n=re.subn(r"assert sha\(B / 'root207_metadata.py'\) == '[0-9a-f]{64}'","assert sha(B / 'root207_metadata.py') == '"+sha(B/'root207_metadata.py')+"'",s);assert n==1;put('run_native207_once.py',s)
v=load('ROOT-207-FRESH-ADMISSION-TEMPLATE.json');v['actor']=ref(B/'run_native207_once.py');put('ROOT-207-FRESH-ADMISSION-TEMPLATE.json',v)
for p in B.rglob('*.py'):compile(p.read_bytes(),str(p),'exec')
print(json.dumps(dict(state='SOURCE_DEPENDENCY_PINNED_NOT_RUNTIME',review=review,Root_source_acceptance=accepted,metadata_sha256=sha(B/'root207_metadata.py'),actor_sha256=sha(B/'run_native207_once.py'))))
