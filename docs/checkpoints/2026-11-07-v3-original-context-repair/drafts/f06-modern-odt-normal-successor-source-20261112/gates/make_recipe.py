"""Prepare/finalize one exact four-gate synthetic recipe; real206 is context only."""
import argparse,hashlib,json,os,sys
from pathlib import Path
os.umask(0o077);sys.dont_write_bytecode=True
W=Path(__file__).resolve().parent;B=W.parent;S=Path('/home/jericho/.cache/FRW-SOL-V3-F06-NORMAL-SUCCESSOR-SOURCE-20261112');sys.path.insert(0,str(W))
from gate_common import KINDS,LIMITS,LIMIT_SCOPE,AUTHORITY,require,sha,ref,json_read

def options(a):
 d={};i=1
 while i<len(a):
  k=a[i];require(k.startswith('--') and k not in d,'duplicate option')
  if i+1<len(a) and not a[i+1].startswith('--'):d[k]=a[i+1];i+=2
  else:d[k]=True;i+=1
 return d

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--draft',action='store_true');p.add_argument('--review',type=Path);a=p.parse_args()
 prior=json_read(S/'gate-preparation/FINAL-GATE-RECIPE.json');pins=dict(prior['pins'])
 for n,h in pins.items():require(sha(n)==h,'old source input drift '+n)
 freeze=ref(B/'SOURCE-FREEZE.json');pins[freeze['path']]=freeze['sha256']
 for r in json_read(freeze['path'])['rows']:require(sha(r['path'])==r['sha256'],'new source freeze drift');pins[r['path']]=r['sha256']
 for name in ('PROJECT495-ORIGINS.json','PUBLIC495-ORIGINS.json'):
  for r in json_read(B/name)['rows'].values():require(sha(r['path'])==r['sha256'],'origin drift');pins[r['path']]=r['sha256']
 review=None
 if not a.draft:
  require(a.review is not None,'independent review required');review=ref(a.review);rv=json_read(a.review)
  require(rv['state']=='APPROVED_SOURCE_AND_GATE_PREPARATION' and rv['blocking_findings']==[] and rv['source_freeze']==freeze,'review differs')
  pins[review['path']]=review['sha256']
 runs={}
 for kind in KINDS:
  opts=options(prior['runs'][kind]['argv']);opts.pop('--eighth-rollback',None)
  opts.update({'--publisher':str(B/'publication/friday_v3_layer_publication.py'),'--run-root':str(W/'runs'/kind),'--ninth-helpers-root':str(B/('public' if kind.startswith('public') else 'project495')),'--ninth-layer-root':str(B/'pair'),'--ninth-native-before':str(B/'native-before'),'--ninth-native-after':str(B/'native-after'),'--ninth-native-spec':str(B/'FINAL-NATIVE-SPEC.json'),'--reuse-eighth-negatives':True})
  if kind.endswith('rollback'):opts['--ninth-rollback']=True
  argv=[str(W/'controls/check_current_source_edges.py')]
  for k,v in opts.items():argv.append(k);argv.extend([] if v is True else [str(v)])
  runs[kind]={'kind':kind,'argv':argv}
 value={'schema':'frw.modern-odt.ninth.synthetic-whole-gate-recipe.v1','assignment':'ASTRA-F06-MODERN-ODT-NORMAL-SUCCESSOR-SOURCE-20261112#1','state':'SOURCE_ONLY_PREPARED_NOT_EXECUTABLE' if a.draft else 'SOURCE_ONLY_REVIEWED_FINAL_RECIPE','authority':AUTHORITY,'authorization':'Root finite task explicit 4 FULL SYNTHETIC gates only; no real installation/admission/UUID/grant','limits':LIMITS,'limit_scope':LIMIT_SCOPE,'run_order':list(KINDS),'single_process_at_a_time':True,'pins':pins,'python':prior['python'],'python_prefix':prior['python_prefix'],'runs':runs,'independent_review':review,'source_freeze':freeze,'actual206_context_only':{'not_fresh_admission':True,'root_closure':{'path':'/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/CORE206-ACTUAL-INSTALLED-CLOSED-20261112.json','sha256':'20e1a9ca845f52eeb0b6a149acc47fd91c9bc70142140e18095acdf18476b900'},'canonical_request':{'path':'H/preparation/ordinary-source-update-v45-4672af5f44cfc8c3/request.json','sha256':'4672af5f44cfc8c3e5e53bf274f7f8338b084a24caa3ae259b5606d7c8246a10'},'receipt_sha256':'253f6586a4fb2b7f9004d47f0cf152a7671d92c774b892b95fa086324dc0bf21'},'coverage':'Actual bounded CP.run+builder+defaultspec/inspect through eight synthetic ancestors and new ninth source operation; no installed/native/Office/user acceptance. Prior unchanged negative matrices and crypto85+12 reused exactscope.'}
 out=W/('DRAFT-GATE-RECIPE.json' if a.draft else 'FINAL-GATE-RECIPE.json');require(not out.exists(),'recipe already exists')
 out.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');out.chmod(0o600);print(json.dumps({'recipe':ref(out),'pins':len(pins),'state':value['state']}))
if __name__=='__main__':main()
