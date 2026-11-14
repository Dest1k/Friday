"""Finite exact frozen-source constructor adapting the existing222 frame.

Only a new own bound-source-frame223-* cache directory is written. Does not
invoke product, builder, current observation, services, once, grant or clocks.
No default inputs, canonical aliases or synthetic final source are accepted.
"""
from pathlib import Path
import argparse,ast,copy,hashlib,json,os,re,stat,types
B=Path(__file__).parent;D=B/'frame-draft'
DRAFT_LOGICAL_FRAME_PREFIX='/home/jericho/.cache/FRW-ASTRA-NATIVE223-MAINTENANCE-FRAME-SOURCE-PREP-20261115/frame-draft'
BASELINE_SOURCE_PINS_REF={'path':'/home/jericho/.cache/FRW-ASTRA-NATIVE222-INSTALL-FRAME-PREP-20261114/frame/SOURCE-PINS.json','sha256':'5e358ccfc80558741e1c34e152d7297b8c733b1490d37d27831a6749cf5b6d00'}
CAP=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE223-ACTUAL222-PREDECESSOR-CAPTURE-20261115/ACTUAL222-ROOT-CANONICAL-CAPTURE.json')
CAP_SHA='32b80537a4e8c51246b21830b80b3fb48d8e3d6ffdc600006e660d9f7debca25'
PRIVATE525='/home/jericho/.cache/FRW-ASTRA-NATIVE222-ACTUAL-CALLER-GATE-20261114/project'
PUBLIC525='/home/jericho/.cache/FRW-ASTRA-NATIVE222-ROOT-ACTUAL221-ORIGIN-CAPTURE-20261114/public-project525'
PUBLIC525_INPUT={'path':'/home/jericho/.cache/FRW-ASTRA-NATIVE222-ROOT-ACTUAL221-ORIGIN-CAPTURE-20261114/INPUT-SOURCE222.public.SOURCE-ONLY.json','sha256':'4d69d6585ca23f304fd6348343d5ea4d6ef4fba3467edece0c1270f5f2e9d724'}
LAYER='ordinary-f04-owned-ingress-stop-terminal-after-source222'
OLD_GUARD='466c67eb3f70713c88573ff6b19ba623762b0e127dc031873f2ed70015ec2743'
def require(ok,why):
 if not ok:raise ValueError(why)
def encoded(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(v,n=64):return type(v)is str and len(v)==n and all(x in '0123456789abcdef'for x in v)
def cache_path(v):
 p=Path(v);require(type(v)is str and p.is_absolute() and str(p)==v and v.startswith('/home/jericho/.cache/') and '/.runtime/'not in v and '..'not in p.parts,'source_cache_path_only')
 for q in reversed((p,*p.parents)):
  require(not q.is_symlink(),'source_ancestor_symlink_rejected')
 return p
def read(v):
 p=cache_path(str(v));a=p.lstat();identity=lambda s:(s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 require(stat.S_ISREG(a.st_mode) and a.st_uid==os.getuid() and a.st_nlink==1,'owned_singlelink_regular_source')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 with os.fdopen(fd,'rb')as f:
  require(identity(a)==identity(os.fstat(f.fileno())),'source_changed_before_open');raw=f.read();require(identity(a)==identity(os.fstat(f.fileno()))==identity(p.lstat()),'source_changed_during_read')
 return raw
def refraw(ref):
 require(type(ref)is dict and set(ref)in ({'path','sha256'},{'path','sha256','bytes'}) and digest(ref['sha256']),'exact_source_ref_required');raw=read(ref['path']);require(sha(raw)==ref['sha256'] and ('bytes'not in ref or type(ref['bytes'])is int and len(raw)==ref['bytes']),'source_ref_changed');return raw
def sized(path,raw):return dict(path=str(path),sha256=sha(raw),bytes=len(raw))
def module(name,raw,path):
 ast.parse(raw);m=types.ModuleType(name);m.__file__=str(path);exec(compile(raw,str(path),'exec'),m.__dict__);return m
def accepted_baseline_source(add):
 raw=refraw(BASELINE_SOURCE_PINS_REF)
 # Authenticate the accepted5e bytes before parsing or profile/bank lookup.
 add(BASELINE_SOURCE_PINS_REF['path'],raw)
 return json.loads(raw)
def rebase_frame_text(text,out):
 # R1 frame source bytes retain R0's immutable logical prefix. Historical and
 # canonical paths outside this own frame prefix remain untouched.
 return text.replace(str(D),str(out)).replace(DRAFT_LOGICAL_FRAME_PREFIX,str(out))
def construct(record_ref,output):
 record=json.loads(refraw(record_ref));require(record['schema']=='frw.Root.native223.frozen-maintenance-source-inputs.v1' and record['source_only']is True and record['execution_grant']is False,'Root_explicit_frozen_SOURCE_record_required')
 require(set(record)=={'schema','source_only','execution_grant','product_source_commit','refs','project_roots','native_after','publication','draft_snapshot'},'exact_finite_constructor_fields')
 snapshot=json.loads(refraw(record['draft_snapshot']));require(snapshot['state']=='UNBOUND_DRAFT_NOT_FINAL_SOURCE_PINS' and snapshot['execution_grant']is False,'exact_reviewed_draft_snapshot_required')
 def draft_read(path):
  path=Path(path);raw=read(path);require(snapshot['files'].get(str(path.relative_to(B)))==sha(raw),'reviewed_draft_source_changed');return raw
 require(snapshot['files'].get('construct_frame223.py')==sha(read(Path(__file__))),'exact_constructor_in_reviewed_snapshot_required')
 require(digest(record['product_source_commit'],40) and record['product_source_commit']!='199405849b62edb926a234f119b5a62d2adcf3b5','actual_distinct_final_product_commit_required')
 require(set(record['refs'])=={'request','private_input','public_input','before_public_input','public_origin','public_delta','manifest','patch'} and record['refs']['before_public_input']==PUBLIC525_INPUT,'exact_final_refs_and_real_public525_before_required')
 require(set(record['project_roots'])=={'private','public'} and set(record['publication'])=={'build-layer-publication-request.py','friday_v3_layer_publication.py'},'two_distinct_source_roots_and_bound_publication')
 out=cache_path(str(output));require(out.parent==B and out.name.startswith('bound-source-frame223-') and not os.path.lexists(out),'fresh_own_bound_frame_only_no_overwrite')
 for root in record['project_roots'].values():cache_path(root);require(root not in (PRIVATE525,PUBLIC525),'new527_source_roots_required')
 require(record['project_roots']['private']!=record['project_roots']['public'],'distinct_private_public_source_roots')
 sources={}
 def add(p,raw):
  p=str(p);require(p not in sources or sources[p]==raw,'conflicting_source_path_bytes');sources[p]=raw
 oldpins=accepted_baseline_source(add)
 add(record_ref['path'],refraw(record_ref));add(record['draft_snapshot']['path'],refraw(record['draft_snapshot']));add(Path(__file__),read(Path(__file__)))
 capraw=refraw(dict(path=str(CAP),sha256=CAP_SHA));cap=json.loads(capraw);add(CAP,capraw)
 actual={};binding=dict(schema='frw.Root.actual222.eight-row-binding.v1',source_commit=cap['actual_product_source_commit'],installed=cap['actual_installed_counts'],not_fresh_future_precondition=True,no_new_effect_or_admission=True)
 for k,row in cap['roles'].items():
  raw=refraw(dict(path=row['cache_path'],sha256=row['sha256'],bytes=row['bytes']));actual[k]=raw;add(row['cache_path'],raw);binding[k]={n:row[n]for n in ('cache_path','canonical_path','sha256','bytes')}
 values={k:json.loads(refraw(r))for k,r in record['refs'].items()if k!='patch'}
 for k,r in record['refs'].items():add(r['path'],refraw(r))
 previous=json.loads(actual['input']);before=json.loads(actual['receipt']);q=values['request'];rows=values['manifest']['files'];native=module('Native223Draft',draft_read(D/'native223_binding.py'),out/'native223_binding.py');counts=native.validate_native_rows(rows,before['files'])
 require(set(record['native_after'])=={r['path']for r in rows},'exact_finalmanifest_native_after_scope')
 for r in rows:
  ref=record['native_after'][r['path']];raw=refraw(ref);require(sha(raw)==r['sha256'] and len(raw)==r['bytes'],'native_after_tuple_bytes_join');add(ref['path'],raw)
 # Projection guard identity follows the actual222 inventory role, then the exact final afterimage.
 guard_roles=[n for n,v in before['files'].items()if v['sha256']==OLD_GUARD];require(len(guard_roles)==1,'unique_actual222_generic_projection_role')
 guard=guard_roles[0];post_guard=next((r['sha256']for r in rows if r['path']==guard),OLD_GUARD)
 require(record['refs']['manifest']['path']==str(Path(record['project_roots']['private'])/('patches/hermes/'+LAYER+'-manifest.json')) and record['refs']['patch']['path']==str(Path(record['project_roots']['private'])/('patches/hermes/'+LAYER+'.patch')),'selected_pair_must_be_inside_exact_private527_source')
 clean=lambda r:{k:r[k]for k in ('path','sha256')}
 require(q['current_input']==q['candidate_input']==clean(record['refs']['private_input']) and values['public_origin']['project']==record['project_roots']['public'],'exact_request_private_input_and_public_origin_root_join')
 require(values['public_delta']['before']==sized(record['refs']['before_public_input']['path'],sources[record['refs']['before_public_input']['path']]) and values['public_delta']['after']==sized(record['refs']['public_origin']['path'],sources[record['refs']['public_origin']['path']]),'public_delta_exact_before_after_ref_join')
 private=values['private_input']['project_files'];public=values['public_input']['project_files'];require(len(private)==len(public)==527 and q['candidate_project']==record['project_roots']['private'],'actual_final527_source_roots_join')
 h='scripts/friday_ordinary_install.py';require(previous['project_files'][h]=='06fd2ab2ab96f9bced79a6d76a74fdc3f6886d468dcd8525a28422d89213ad43' and private[h]!=public[h],'actual222_before_helper_and_distinct527_after')
 def inventory(root,expected):
  root=cache_path(root);seen=set();refs={}
  for parent,dirs,files in os.walk(root,followlinks=False):
   for n in dirs:require(not (Path(parent)/n).is_symlink(),'project_directory_symlink')
   seen.update(str((Path(parent)/n).relative_to(root))for n in files)
  require(seen==set(expected),'exact_project_inventory_required')
  for n,v in expected.items():
   require(n and not n.startswith('/') and all(x not in ('','.','..')for x in n.split('/')),'safe_project_relative');p=root/n;raw=read(p);require(sha(raw)==v,'project_source_changed:'+n);refs[n]=sized(p,raw);add(p,raw)
  return refs
 project_sources={f:inventory(record['project_roots'][f],v)for f,v in (('private',private),('public',public))};project_sources['previous']=inventory(PRIVATE525,previous['project_files'])
 pub={k:refraw(r)for k,r in record['publication'].items()}
 for k,raw in pub.items():ast.parse(raw)
 substitutions={'REQUEST_SHA':record['refs']['request']['sha256'],'INPUT_SHA':record['refs']['private_input']['sha256'],'PRIVATE_HELPER':private[h],'PUBLIC_HELPER':public[h],'CONSUMER_SHA':sha(pub['friday_v3_layer_publication.py']),'CONSUMER':str(out/'publication/friday_v3_layer_publication.py'),'REQUEST':str(out/'ROOT-FRESH-REQUEST.json'),'COMMIT':record['product_source_commit'],'PRODUCT223_COMMIT':record['product_source_commit'],'NATIVE_PROJECTION_SHA256':post_guard,'OBSERVER_SHA256':None}
 rendered={}
 for path in sorted(D.rglob('*.py')):
  rel=str(path.relative_to(D));raw=rebase_frame_text(draft_read(path).decode(),out)
  for k,v in substitutions.items():
   if v is not None:raw=raw.replace('UNBOUND_NATIVE223_'+k,v)
  raw=raw.replace('SOURCE_BOUND = False','SOURCE_BOUND = True')
  rendered[rel]=raw.encode()
 substitutions['OBSERVER_SHA256']=sha(rendered['admission-retained/observe-current-retained-units.py'])
 rendered['run_native223_once.py']=rendered['run_native223_once.py'].replace(b'UNBOUND_NATIVE223_OBSERVER_SHA256',substitutions['OBSERVER_SHA256'].encode())
 pred=module('Exact222Source',rendered['predecessor222.py'],out/'predecessor222.py').validate_actual222(binding,actual)
 n=module('BoundNative223',rendered['native223_binding.py'],out/'native223_binding.py');static=n.bind_static(request_raw=sources[record['refs']['request']['path']],input_raw=sources[record['refs']['private_input']['path']],manifest_raw=sources[record['refs']['manifest']['path']],patch_raw=sources[record['refs']['patch']['path']],predecessor_six=pred,actual_rows=actual)
 static_raw=encoded(static);rendered['native223_binding.py']=rendered['native223_binding.py'].replace(b'UNBOUND_NATIVE223_STATIC_BINDING_SHA256',sha(static_raw).encode())
 spec=dict(schema='frw.f04223.pair-spec.v1',source_only=True,current_authority=False,execution_grant=False,installed223=False,layer=LAYER,outer_schema='friday.ordinary-telegram-source-update.v46',successor_schema='friday.current-source-native-successor.v25',native_files=rows,selected_targets=counts['touched']+6,manifest=sized(record['refs']['manifest']['path'],sources[record['refs']['manifest']['path']]),patch=sized(record['refs']['patch']['path'],sources[record['refs']['patch']['path']]),manifest_rel='patches/hermes/'+LAYER+'-manifest.json',counts=dict(added=counts['added'],modified=counts['modified'],retained=17893-counts['modified'],before_layers=222,after_layers=223,before_project=525,after_project=527,before_native=17893,after_native=17893+counts['added'],base=17730,plugins=52))
 local={'SOURCE-SPEC223.json':encoded(spec),'STATIC-BINDING223.json':static_raw,'ACTUAL222-EIGHT-ROW-BINDING.json':encoded(binding),'ROOT-FRESH-REQUEST.json':sources[record['refs']['request']['path']]}
 fixed={k:record['refs'][k]for k in ('request','private_input','public_input','before_public_input','public_origin','public_delta')};fixed.update(native_spec=sized(out/'SOURCE-SPEC223.json',local['SOURCE-SPEC223.json']),static_binding=sized(out/'STATIC-BINDING223.json',static_raw),actual222_binding=sized(out/'ACTUAL222-EIGHT-ROW-BINDING.json',local['ACTUAL222-EIGHT-ROW-BINDING.json']))
 # Descriptor consumers use clean two-field refs for fixed JSON roles.
 fixed={k:{n:r[n]for n in ('path','sha256')}for k,r in fixed.items()}
 descriptor=dict(schema='frw.root223.typed-origin-source-descriptor.v1',source_only=True,execution_grant=False,current_admission=False,future_root_authority=dict(source_acceptance='UNBOUND_ROOT',current='UNBOUND_ROOT',once='UNBOUND_ROOT',grant='UNBOUND_ROOT',clock='UNBOUND_ROOT'),project_roots={**record['project_roots'],'previous':PRIVATE525},dependencies={k:sized(out/(k+'.py'),rendered[k+'.py'])for k in ('predecessor222','native223_binding')},fixed=fixed,actual_rows={k:dict(path=r['cache_path'],sha256=r['sha256'],bytes=r['bytes'])for k,r in binding.items()if k in actual},project_sources=project_sources,native_after={n:sized(r['path'],sources[r['path']])for n,r in record['native_after'].items()})
 local['ROOT223-DATA-BINDINGS.json']=encoded(descriptor)
 for k,raw in pub.items():rendered['publication/'+k]=raw
 # Bind pure projection against actual supplied inventories, before any output.
 modes={f:{n:('100755'if Path(r['path']).lstat().st_mode&0o111 else '100644')for n,r in project_sources[f].items()}for f in ('private','public')}
 module('Bound223Projection',rendered['root223_projection.py'],out/'root223_projection.py').validate(predecessor=pred,static_binding=static,request=q,private_input=values['private_input'],public_input=values['public_input'],before_public_input=values['before_public_input'],public_origin=values['public_origin'],public_delta=values['public_delta'],spec=spec,project_bytes={f:{n:sources[r['path']]for n,r in project_sources[f].items()}for f in ('private','public')},project_modes=modes)
 history_name='ROOT-223-CONSUMED-HISTORY-TEMPLATE.json';history=json.loads(draft_read(D/history_name));history['actual222_binding']=fixed['actual222_binding'];local[history_name]=encoded(history)
 for p in D.glob('*TEMPLATE.json'):
  if 'CONSUMED-HISTORY'in p.name:
   value=json.loads(draft_read(p));value['actual222_binding']=fixed['actual222_binding'];local[p.name]=encoded(value);continue
  value=json.loads(rebase_frame_text(draft_read(p).decode(),out))
  def fill(v):
   if type(v)is list:return [fill(x)for x in v]
   if type(v)is dict:
    v={k:fill(x)for k,x in v.items()}
    if 'path'in v and 'sha256'in v and type(v['path'])is str and v['path'].startswith(str(out)+'/'):
     name=v['path'][len(str(out))+1:];v['sha256']=sha(local[name])if name in local else sha(rendered[name])if name in rendered else 'UNBOUND_ROOT_'+name
    return v
   return v
  value=fill(value)
  if 'SOURCE-ACCEPTANCE'in p.name:
   value['source_pins']=fixed;value['project_source_proof']=fixed['public_origin'];value['origin_policy']=dict(path=str(out/'SOURCE-ORIGIN-POLICY223.json'),sha256='UNBOUND_STATIC_ORIGIN_POLICY')
  if 'product_source_commit'in value:value['product_source_commit']=record['product_source_commit']
  if 'expected_receipt_sha256'in value:value['expected_receipt_sha256']=static['prospective_receipt_sha256']
  if 'native_spec'in value:value['native_spec']=fixed['native_spec']
  if 'operational_input'in value:value['operational_input']=q['current_input']
  if 'actual222_predecessor'in value:value['actual222_predecessor']=fixed['actual222_binding']
  local[p.name]=encoded(value)
 local['SOURCE-ORIGIN-POLICY223.json']=encoded(dict(schema='frw.root223.source-origin-policy.v1',source_only=True,current_admission=False,execution_grant=False,product_source_commit=record['product_source_commit'],predecessor_source_commit=pred['source_commit'],immutable_public_capture=record['refs']['public_origin'],immutable_delta=record['refs']['public_delta'],previous_private_project_files=525,private_project_files=527,public_project_files=527,private_public_flavors=28,new_delta=[h,'patches/hermes/'+LAYER+'-manifest.json','patches/hermes/'+LAYER+'.patch'],future_current_raw_git_and_working_source_check='UNBOUND_ROOT_EXPLICIT_FUTURE_SOURCE_ORIGIN_CALL'))
 # The acceptance template's origin ref is exact static source, never a current/grant claim.
 acceptance_name='ROOT-223-SOURCE-ACCEPTANCE-TEMPLATE.json';acceptance=json.loads(local[acceptance_name]);acceptance['origin_policy']=dict(path=str(out/'SOURCE-ORIGIN-POLICY223.json'),sha256=sha(local['SOURCE-ORIGIN-POLICY223.json']));local[acceptance_name]=encoded(acceptance)
 # Reuse exact immutable profile/bank evidence only, never cached current truth.
 profile='/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT207-ROOT-SOURCE-AFTER206-20261112/PROFILE-SOURCE-JOIN.json';bank='/home/jericho/.cache/FRW-ASTRA-V3-CORE-FILE-INTEGRATION-20261111/presentation-bank-direct/EXPECTED-BANK-MANIFEST.json'
 for p in (profile,bank):add(p,refraw(dict(path=p,sha256=oldpins['source_refs'][p])))
 for r in json.loads(sources[profile])['evidence']:add(r['path'],refraw(r))
 current=module('Bound223CurrentProducer',rendered['prepare_root223.py'],out/'prepare_root223.py')
 for name,digest_value in current.RECOVERY_DEPENDENCIES.items():
  path=current.OLD/name;add(path,refraw(dict(path=str(path),sha256=digest_value)))
 path=current.OLD/'root221_recovery_scope.py';add(path,refraw(dict(path=str(path),sha256=current.RECOVERY_SHA)))
 # Future source commands are assembled only; default223 remains postcommit.
 py=n.PYTHON;local['ROOT-FUTURE-COMMANDS.json']=encoded(dict(schema='frw.root223.source-only-future-commands.v1',execution_grant=False,commands=dict(builder=[py,'-I','-B',str(out/'publication/build-layer-publication-request.py')],publisher=[py,'-I','-B',str(out/'publication/friday_v3_layer_publication.py'),'--request',str(out/'ROOT-FRESH-REQUEST.json'),'--request-sha256',substitutions['REQUEST_SHA']],postcommit_default=[py,'-I','-B',str(Path(record['project_roots']['private'])/'scripts/friday_install.py'),'check','--input',q['current_input']['path']]),future_default223_phase='POSTCONDITION_OF_SAME_ADMITTED_COMMIT_NOT_PREINSTALL_PASS'))
 for rel,raw in {**rendered,**local}.items():add(out/rel,raw)
 for rel,raw in rendered.items():ast.parse(raw);require('UNBOUND_NATIVE223_'not in raw.decode(),'unbound_final_executable_source_constant:'+rel)
 producer=module('Bound223Pins',rendered['source_pins_producer.py'],out/'source_pins_producer.py');pins=producer.assemble(frame=str(out),source_bytes=sources,historical_bytes={},source_spec_ref=fixed['native_spec'],product_source_commit=record['product_source_commit']);local['SOURCE-PINS.json']=encoded(pins)
 virtual=module('Bound223DataBeforeOutput',rendered['root223_data.py'],out/'root223_data.py');virtual_raw={**sources,str(out/'SOURCE-PINS.json'):local['SOURCE-PINS.json']}
 def planned_cache_raw(path):
  path=str(path);require(path in virtual_raw,'constructor_followed_unpinned_source');return virtual_raw[path]
 virtual.cache_raw=planned_cache_raw
 consumed=virtual.load(sha(local['SOURCE-PINS.json']),frame=out);require(consumed['static_binding']==static,'complete_planned_data_consumer_before_output')
 # All validation above precedes own output. No current/authority/once leaves.
 out.mkdir(mode=0o700)
 for rel,raw in {**rendered,**local}.items():
  p=out/rel;p.parent.mkdir(mode=0o700,parents=True,exist_ok=True);fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  with os.fdopen(fd,'wb')as f:f.write(raw)
 return dict(state='SOURCE_ASSEMBLED_REQUIRES_FINAL_FRAME_REVIEW_AND_ACTUAL_BUILDER_CONSUMER',frame=str(out),source_pins=sized(out/'SOURCE-PINS.json',local['SOURCE-PINS.json']),current_admission=False,execution_grant=False,once='ABSENT',current_records='ABSENT',native_scope=counts,post_generic_projection_sha256=post_guard)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--frozen-source-record',required=True);p.add_argument('--frozen-source-record-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(construct(dict(path=a.frozen_source_record,sha256=a.frozen_source_record_sha256),Path(a.output)),sort_keys=True))
