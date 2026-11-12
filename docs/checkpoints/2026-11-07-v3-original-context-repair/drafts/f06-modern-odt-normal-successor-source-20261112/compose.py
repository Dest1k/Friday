"""One source-only exact normal successor after prospective206; no live authority."""
import ast,copy,datetime,difflib,hashlib,json,os,re
from pathlib import Path
os.umask(0o077)
B=Path(__file__).resolve().parent
S=Path('/home/jericho/.cache/FRW-SOL-V3-F06-NORMAL-SUCCESSOR-SOURCE-20261112')
M=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-MODERN-ODF-REQUIRED-PATH-SOURCE-20261112')
L='f06-modern-odt-authenticated-profile-after-source206';MN='patches/hermes/'+L+'-manifest.json';PT='patches/hermes/'+L+'.patch'
CP='docs/checkpoints/2026-11-07-v3-original-context-repair'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def enc(v):return (json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()
def save(p,v):
 assert p.is_relative_to(B);p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 data=v if isinstance(v,bytes) else enc(v)
 if p.exists():
  p.write_bytes(data);return
 with p.open('xb') as f:f.write(data)
def delta(a,b,n):return ''.join(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),fromfile='a/'+n,tofile='b/'+n)).encode()
def main():
 assert sha(S/'RESULT.json')=='64fe5b5688db6b711b0204e1bd4db9100c28d21881574f047b2789f7a2d5c107'
 assert sha(M/'RESULT.json')=='6f9aa6bb55529b35086449e74004258146f9851875364e9f309534a971c1bff6'
 old=S/'native-after/tools/scoped_odf_password.py';new=M/'candidate/tools/scoped_odf_password.py'
 assert sha(old)=='ea59d8aa1225ea1ef25227b8a65cb94fcabef5932d90d2ad901ab0cfbd98b1ae'
 assert sha(new)=='b66d95d1f2a4223ffcc9d54e28d13976b49e5e2f041e1c12456a8c7b85922d9d'
 save(B/'native-before/tools/scoped_odf_password.py',old.read_bytes());save(B/'native-after/tools/scoped_odf_password.py',new.read_bytes())
 patch=delta(old.read_bytes(),new.read_bytes(),'tools/scoped_odf_password.py');save(B/'pair'/PT,patch)
 before=json.loads((S/'NATIVE206-PROSPECTIVE-COMPOSITION.json').read_bytes())['expected_inventory']
 origins=json.loads((S/'PROJECT493-ORIGINS.json').read_bytes())['rows'];puborig=json.loads((S/'PUBLIC493-ORIGINS.json').read_bytes())['rows']
 prereq={}
 for r in before['layers']:
  d=json.loads(Path(origins[r['manifest']]['path']).read_bytes());p=d.get('patch',d.get('patch_file'))
  if '/' not in p:p=str(Path(r['manifest']).parent/p)
  assert sha(Path(origins[r['manifest']]['path']))==r['manifest_sha256'];assert sha(Path(origins[p]['path']))==r['patch_sha256']==d['patch_sha256'];assert p not in prereq
  prereq[p]=r['patch_sha256']
 row={'path':'tools/scoped_odf_password.py','before_sha256':sha(old),'sha256':sha(new),'bytes':new.stat().st_size,'mode':'100644','new_file':False}
 manifest={'base_commit':before['commit'],'files':[row],'patch':PT,'patch_sha256':sha(B/'pair'/PT),'prerequisites':prereq};save(B/'pair'/MN,manifest)
 assert len(prereq)==206
 # Derive next fixed consumer with same fixed seal/CAS contract.
 impl=(S/'ordinary-edge/implement.py').read_text()
 ordinal={'EIGHTH':'NINTH','Eighth':'Ninth','eighth':'ninth','SEVENTH':'EIGHTH','Seventh':'Eighth','seventh':'eighth','SIXTH':'SEVENTH','Sixth':'Seventh','sixth':'seventh','FIFTH':'SIXTH','Fifth':'Sixth','fifth':'sixth'}
 impl=re.sub('|'.join(ordinal),lambda m:ordinal[m.group()],impl)
 start=impl.index('SRC=');end=impl.index('changes={}')
 impl=impl[:start]+f"SRC=Path({str(S)!r})\nnative={ {row['path']:(row['before_sha256'],row['sha256'],row['bytes'],False)}!r}\nconst=\"CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v9'\\nCURRENT_SOURCE_NINTH_LAYER = '{L}'\\nCURRENT_SOURCE_NINTH_MANIFEST = '{sha(B/'pair'/MN)}'\\nCURRENT_SOURCE_NINTH_PATCH = '{sha(B/'pair'/PT)}'\\nCURRENT_SOURCE_NINTH_NATIVE = \"+repr(native)+\"\\n\"\n"+impl[end:]
 impl=impl.replace("('public','public','0f11a8e80b2a01e4b49cbb827d331b46ddb085d076eb8f0492c59e4b57e6082e'),('private','project491','f570120371c28eeeb9f708ffbd32d451056c39fc57f7a49ed60eb9db0eb26cb5')", "('public','public','40a404292832b258e48c4f5af7bac3fdf263ce30a4077bde0af0ab8eaed0a174'),('private','project493','489f6a23a4015bbb1daad9c405028b83e55b10725cd4f5e8b56ce678ee6e1eb9')")
 impl=impl.replace('seven authenticated','eight authenticated').replace('eight authenticated native CP edges\')','nine authenticated native CP edges\')')
 impl=impl.replace("CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v7'", "CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v8'")
 impl=impl.replace("'CP204 -> selected CP205','CP204 -> CP205 -> selected CP206'", "'CP205 -> selected CP206','CP205 -> CP206 -> selected CP207'").replace("'Historical CP204','Historical CP205'", "'Historical CP205','Historical CP206'")
 impl=impl.replace("replace('CP204','CP205')", "replace('CP205','CP206')").replace("replace('CP203','CP204')", "replace('CP204','CP205')")
 impl=impl.replace('v6 root and seven fixed','v6 root and eight fixed').replace('v6 root and eight fixed authenticated native CP edges.\'\'\'','v6 root and nine fixed authenticated native CP edges.\'\'\'')
 impl=impl.replace('v6 root and eight fixed authenticated native CP edges.\"\"\"\'\',','v6 root and nine fixed authenticated native CP edges.\"\"\"\'\',')
 impl=impl.replace("end=s.index('\\ndef _current_source_eighth_successor_checked',start)","end=s.index('\\n_CURRENT_SOURCE_SEVENTH_HISTORY_SEAL',start)")
 impl=impl.replace('not fourth and not sixth and not seventh and not eighth','not fourth and not fifth and not sixth and not seventh and not eighth')
 # Exact literals in retained generated pattern, preserving all earlier branches.
 impl=impl.replace("replace('before_layers = 204 if eighth else','before_layers = 205 if ninth else 204 if eighth else')", "replace('before_layers = 205 if eighth else','before_layers = 206 if ninth else 205 if eighth else')")
 impl=impl.replace("replace('before_native_count = 17891 if eighth or seventh else','before_native_count = 17891 if ninth or eighth or seventh else')", "replace('before_native_count = 17891 if eighth or seventh or sixth else','before_native_count = 17891 if ninth or eighth or seventh or sixth else')")
 impl=impl.replace("replace('before_project_count = 489 if eighth else','before_project_count = 491 if ninth else 489 if eighth else')", "replace('before_project_count = 491 if eighth else','before_project_count = 493 if ninth else 491 if eighth else')")
 impl=impl.replace('v6 root and eight fixed authenticated native CP edges.','v6 root and nine fixed authenticated native CP edges.',1) if False else impl
 impl=impl.replace("edges.\"\"\"','\"\"\"The v6 root and eight fixed authenticated native CP edges.","edges.\"\"\"','\"\"\"The v6 root and nine fixed authenticated native CP edges.")
 # Historical native v7 stays v7 in the preserved chain; insertion locates v8.
 impl=impl.replace('B=Path(__file__).resolve().parent',"B=Path(__file__).resolve().parent/'ordinary-edge'")
 save(B/'implement_helper.py',impl.encode())
 exec(compile(impl,str(B/'implement_helper.py'),'exec'),{'__file__':str(B/'implement_helper.py')})
 for kind,source in [('project495','private'),('public','public')]:
  save(B/kind/'scripts/friday_install.py',(S/('project493' if kind=='project495' else 'public')/'scripts/friday_install.py').read_bytes())
  save(B/kind/'scripts/friday_ordinary_install.py',(B/'ordinary-edge'/source/'scripts/friday_ordinary_install.py').read_bytes())
 for name in ('friday_v3_layer_publication.py','build-layer-publication-request.py'):
  s=(S/'publication'/name).read_text()
  if name=='friday_v3_layer_publication.py':
   assert s.count('    "f06-protected-office-profiles-after-source205",')==1
   s=s.replace('    "f06-protected-office-profiles-after-source205",','    "f06-protected-office-profiles-after-source205",\n    "'+L+'",')
   s=s.replace('"friday.current-source-native-successor.v8")','"friday.current-source-native-successor.v8", "friday.current-source-native-successor.v9")')
  else:
   s=s.replace('or CP205 request','CP205 or CP206 request')
   s=s.replace('"friday.current-source-native-successor.v7": "friday.current-source-native-successor.v8",','"friday.current-source-native-successor.v7": "friday.current-source-native-successor.v8",\n                "friday.current-source-native-successor.v8": "friday.current-source-native-successor.v9",')
   needle='                             "transaction_current_source_exact_eighth_layer_required")'
   assert s.count(needle)==1
   s=s.replace(needle,needle+'\n            consumer.require(previous_schema != "friday.current-source-native-successor.v8"\n                             or args.layer_names == ("'+L+'",),\n                             "transaction_current_source_exact_ninth_layer_required")')
  ast.parse(s);save(B/'publication'/name,s.encode())
 prior=json.loads((S/'INPUT-SOURCE206.PROSPECTIVE.NOT_INSTALLED.json').read_bytes());pubprior=json.loads((S/'INPUT-SOURCE206.PUBLIC.PROSPECTIVE.NOT_INSTALLED.json').read_bytes())
 olddiffs={n for n,h in prior['project_files'].items() if pubprior['project_files'][n]!=h}
 for kind,ori,pv in [('project495',origins,prior),('public',puborig,pubprior)]:
  assert len(ori)==len(pv['project_files'])==493
  for n,r in ori.items():assert sha(Path(r['path']))==r['sha256']==pv['project_files'][n],n
  ori['scripts/friday_ordinary_install.py']=ref(B/kind/'scripts/friday_ordinary_install.py')
  for n in (MN,PT):save(B/kind/n,(B/'pair'/n).read_bytes());ori[n]=ref(B/kind/n)
  pv['project_files']={n:r['sha256'] for n,r in ori.items()}
  save(B/('PROJECT495-ORIGINS.json' if kind=='project495' else 'PUBLIC495-ORIGINS.json'),{'state':'PROSPECTIVE_NOT_INSTALLED_NOT_ADMISSION','rows':ori})
  save(B/('INPUT-SOURCE207.PROSPECTIVE.NOT_INSTALLED.json' if kind=='project495' else 'INPUT-SOURCE207.PUBLIC.PROSPECTIVE.NOT_INSTALLED.json'),pv)
 assert len(olddiffs)==28 and {n for n,h in prior['project_files'].items() if pubprior['project_files'][n]!=h}==olddiffs
 save(B/'COUNTERPART-INVARIANTS.json',{'private_difference_names':sorted(olddiffs),'private_difference_count':len(olddiffs),'all495_origins_verified':True,'native_installer_unchanged':True,'no_full_project_H_requirement':True})
 expected=copy.deepcopy(before);assert expected['files'][row['path']]['sha256']==row['before_sha256'];expected['files'][row['path']].update(sha256=row['sha256'],bytes=row['bytes'],mode=row['mode'])
 expected['layers'].append({'manifest':MN,'manifest_sha256':sha(B/'pair'/MN),'patch_sha256':sha(B/'pair'/PT)})
 save(B/'NATIVE207-PROSPECTIVE-COMPOSITION.json',{'state':'PROSPECTIVE_NOT_INSTALLED_NOT_CANONICAL_RECEIPT','basis':ref(S/'NATIVE206-PROSPECTIVE-COMPOSITION.json'),'expected_inventory':expected})
 save(B/'FINAL-NATIVE-SPEC.json',{'state':'PROSPECTIVE207_SOURCE_NOT_INSTALLED_NOT_ADMITTED','layer':L,'manifest':ref(B/'pair'/MN),'patch':ref(B/'pair'/PT),'manifest_rel':MN,'patch_rel':PT,'native_files':[row],'native_modifications':1,'native_additions':0,'untouched_native_rows':len(expected['files'])-1,'selected_targets':1+1+2+3,'before_expected':{'project':493,'native':len(before['files']),'layers':len(before['layers']),'plugins':52,'base':before['source_file_count']},'after_expected':{'project':len(origins),'native':len(expected['files']),'layers':len(expected['layers']),'plugins':sum(n.startswith('plugins/friday_rework/') for n in origins),'base':expected['source_file_count']},'actual206_CP':None,'actual207_receipt':None,'UUID':None})
 public_patch=delta((S/'public/scripts/friday_ordinary_install.py').read_bytes(),(B/'public/scripts/friday_ordinary_install.py').read_bytes(),'scripts/friday_ordinary_install.py');save(B/'public-helper.patch',public_patch)
 save(B/'operational-helper.patch',delta((S/'project493/scripts/friday_ordinary_install.py').read_bytes(),(B/'project495/scripts/friday_ordinary_install.py').read_bytes(),'scripts/friday_ordinary_install.py'))
 for name in ('friday_v3_layer_publication.py','build-layer-publication-request.py'):public_patch+=delta((S/'publication'/name).read_bytes(),(B/'publication'/name).read_bytes(),CP+'/'+name)
 for n in (MN,PT):public_patch+=''.join(difflib.unified_diff([],(B/'pair'/n).read_text().splitlines(True),fromfile='/dev/null',tofile='b/'+n)).encode()
 save(B/'PUBLIC-INTEGRATION.patch',public_patch)
 print('COMPOSED',ref(B/'PUBLIC-INTEGRATION.patch'))
if __name__=='__main__':main()
