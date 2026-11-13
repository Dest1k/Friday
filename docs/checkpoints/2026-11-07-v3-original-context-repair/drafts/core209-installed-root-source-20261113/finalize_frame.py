"""Finite R2 relocation/freeze only; reuse original external source seals, no H reads."""
from pathlib import Path
import difflib,hashlib,json,os,stat,sys
B=Path(__file__).parent
O=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE209-ROOT-FRAME-PREP-20261113-R1')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ref=lambda p:dict(path=str(p),sha256=sha(p))
def put(n,v):
 p=B/n;p.write_text(v if isinstance(v,str)else json.dumps(v,sort_keys=True,indent=2)+'\n');p.chmod(0o600)
def main():
 if sys.argv[1:]!=['--finalize-source-only-R2']:raise ValueError('explicit_R2_source_only_finalize_required')
 assert sha(O/'SOURCE-PINS.json')=='cc66b9cb42ec75f5a8af6e1133842976cce1949b030905b1b70590f6e873f90b'
 old=json.loads((O/'SOURCE-PINS.json').read_bytes())
 # Four existing source refs are rebound to relocated code; current authority stays UNBOUND.
 rows=[]
 for name,fields in {'ROOT-209-FRESH-ADMISSION-TEMPLATE.json':dict(actor=B/'run_native209_once.py',recovery=B/'resume_native209_services.py'),'ROOT-209-RUNTIME-AUTHORITY-TEMPLATE.json':dict(boundary=B/'core209-first-actual-root.py',caller=B/'start_core209_once.py')}.items():
  v=json.loads((B/name).read_bytes());original=json.loads((O/name).read_bytes())
  for k,p in fields.items():rows.append(dict(template=name,key=k,before=original[k],after=ref(p)));v[k]=ref(p)
  put(name,v)
 put('PARENT-SOURCE-TEMPLATE-BINDING-DELTA.json',dict(state='R2_RELOCATION_AND_SOURCE_HASH_ONLY_NO_NEW_POLICY_OR_AUTHORITY',rows=rows,original_final_ledger=ref(O/'PARENT-SOURCE-TEMPLATE-BINDING-DELTA.json'),metadata_result=ref(Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE209-ROOT-FRAME-PREP-20261113/metadata-work/RESULT.json'))))
 future=json.loads((O/'ROOT-FUTURE-COMMANDS.json').read_bytes());future=json.loads(json.dumps(future).replace(str(O),str(B)));future['order']='Root remaps and genuinely binds existing static6 + R2 exact source review. Same prospective209 normal builder fullspec; retained source497 default spec/inspect on real managedH. OS-style EACCES denies all filesystem mutation; process/socket/env denials hard. Root captures child exitcode before tolerant structured-record parsing. Fresh mutable/source admission remains Root-only.';put('ROOT-FUTURE-COMMANDS.json',future)
 pins=json.loads(json.dumps(old));pins['frame']=str(B);pins['state']='FROZEN_R2_SOURCE_ONLY_R1_AND_B9_PRESERVED_NO_NEW_AUTHORITY';source={};relocated=[];retained=[]
 for name,h in old['source_refs'].items():
  p=Path(name)
  if p.is_relative_to(O)and(B/p.relative_to(O)).is_file():
   q=B/p.relative_to(O);source[str(q)]=sha(q);relocated.append(dict(before=dict(path=name,sha256=h),after=ref(q)))
  else:source[name]=h;retained.append(name)
 for p in (B/'saved-shape-work').glob('*.py'):
  source[str(p)]=sha(p)
 pins['source_refs']=source;pins['historical_refs']=old['historical_refs'];pins['R2_source_reuse']=dict(original_manifest=ref(O/'SOURCE-PINS.json'),original_result=ref(O/'RESULT.json'),external_source_refs_reused_without_full_rehash=len(retained),relocated_source_refs=len(relocated),unchanged_historical_refs=43,original_reviews_reused=[ref(O/'review/RESULT.json')],scope='Relocation plus strict sized source-gate reference consumption and corresponding actor metadata source pin only. R1 guard/candidate/correlation unchanged. No source policy/runtime/admission verdict or consumed R1 caller retry.')
 put('SOURCE-PINS.json',pins)
 diffs=[]
 for row in relocated:
  before=Path(row['before']['path']);after=Path(row['after']['path']);assert before.is_file()
  if before.read_bytes()==after.read_bytes():continue
  n=after.relative_to(B).as_posix().replace('/','__')+'.diff';text=''.join(difflib.unified_diff(before.read_text().splitlines(True),after.read_text().splitlines(True),fromfile='consumed-R1/'+before.relative_to(O).as_posix(),tofile='source-R2/'+after.relative_to(B).as_posix()));put(n,text);diffs.append(dict(before=row['before'],after=row['after'],diff=ref(B/n)))
 put('R2-DIFF-MANIFEST.json',dict(state='EXACT_R1_TO_R2_DELTA_NO_ORIGINAL_MUTATION',original_manifest=ref(O/'SOURCE-PINS.json'),final_manifest=ref(B/'SOURCE-PINS.json'),changed=diffs,relocated=relocated,retained_source_refs=len(retained),historical_refs_unchanged=True))
 print(json.dumps(dict(state=pins['state'],manifest=ref(B/'SOURCE-PINS.json'),source_refs=len(source),retained_source_refs=len(retained),relocated=len(relocated),diffs=len(diffs))))
if __name__=='__main__':main()
