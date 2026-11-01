"""All observations below are in-memory synthetic controls, never runtime authority."""
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone,timedelta
import copy, hashlib,io,json,os,runpy,types,time,zipfile
D=Path(__file__).resolve().parents[1]; C=D/'code'
B=runpy.run_path(str(C/'pptx_pdf_boundary.py'));K=runpy.run_path(str(C/'pptx_pdf_contract.py'))
A=runpy.run_path(str(C/'v02_known_pdf_adapter.py'));Q=runpy.run_path(str(C/'qualify_pptx_pdf.py'))
O=runpy.run_path(str(C/'pptx_pdf_observation.py'));P=runpy.run_path(str(C/'pdf_pages.py'))
OLD=runpy.run_path(str(D/'tests/offline_controls.py'))
CALLER=Path('/private-bindings/dependency-5')
RESULT=[]
def need(x,msg='assertion'):
 if not x:raise AssertionError(msg)
def reject(fn,code=None):
 try:fn()
 except (ValueError,AssertionError,KeyError,TypeError,OSError) as e:
  if code:need(code in str(e),(code,str(e)))
  return
 raise AssertionError('unexpected acceptance')
def control(name,fn):
 try:fn();RESULT.append(dict(name=name,status='PASS'))
 except Exception as e:RESULT.append(dict(name=name,status='FAIL',error=f'{type(e).__name__}: {e}'))
 print(RESULT[-1])
def sha(x):return hashlib.sha256(x).hexdigest()
def enc(x):return json.dumps(x,ensure_ascii=False,sort_keys=True).encode()
def ref(p,raw):return dict(path=str(p),sha256=sha(raw))
class Model:
 def __init__(self):self.raw={}
 def put(self,p,v):
  raw=v if isinstance(v,bytes) else enc(v);p=str(p);self.raw[p]=raw;return ref(p,raw)
 def read(self,r,cap=64*1024*1024,private=False):
  raw=self.raw.get(r['path'])
  if raw is None:raw=Path(r['path']).read_bytes()
  need(len(raw)<=cap and sha(raw)==r['sha256'],'SYNTHETIC_PIN_OR_CAP');return raw
 def document(self,r):return json.loads(self.read(r))
 need=staticmethod(lambda x,s: B['need'](x,s))
 def replace(self,r,fn):
  v=self.document(r);fn(v);self.raw[r['path']]=enc(v);return ref(r['path'],enc(v))

def scenario():
 m=Model(); manifest=json.loads((D/'MANIFEST.json').read_bytes());mr=m.put(D/'MANIFEST.json',manifest)
 # Actual fixture bytes are only source inputs. Genuine control bytes are a
 # distinct inert PPTX mutation held in memory; no user/Office proof is written.
 known=(D/'fixtures/known-visible-label.pptx').read_bytes(); bio=io.BytesIO()
 with zipfile.ZipFile(io.BytesIO(known)) as z,zipfile.ZipFile(bio,'w') as out:
  for info in z.infolist():out.writestr(info,z.read(info.filename).replace(b'Quarterly report',b'Genuine quarterly report'))
 genuine=bio.getvalue(); need(sha(known)!=sha(genuine))
 pages=copy.deepcopy(OLD['PAGE_TEXTS']);pages[0]=pages[0].replace('Quarterly report','Genuine quarterly report')
 epages=copy.deepcopy(OLD['EXPECTED']['pages']);epages[0]['text_tokens'][0]='Genuine quarterly report'
 expected=K['expectation_from_pptx'](genuine,epages,False)
 binding=OLD['make_binding'](mr)
 binding['kernel']={'release':os.uname().release,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
 binding['received_artifact']=m.put('/synthetic-control/genuine.pptx',genuine);binding['received_bytes']=len(genuine)
 binding['delivered_pdf']=m.put('/synthetic-control/genuine-delivered.pdf',b'%PDF-in-memory-genuine-not-runtime-authority');binding['delivered_pdf_bytes']=len(m.read(binding['delivered_pdf']))
 binding['expectation']=m.put('/synthetic-control/genuine-expectation',expected)
 # Known fixture paths remain the accepted source tree paths, never genuine.
 known_input=ref(D/'fixtures/known-visible-label.pptx',known)
 known_expectation=ref(D/'fixtures/KNOWN-PPTX-PDF-EXPECTATION.json',(D/'fixtures/KNOWN-PPTX-PDF-EXPECTATION.json').read_bytes())
 kclock=dict(boot_id=binding['kernel']['boot_id'],origin_monotonic=100.,deadline_monotonic=180.)
 tools={n:binding[n] for n in ('consumer','strace','pdf_reader')};tools['wrapper']=OLD['REF']('/opt/friday-archive/bin/libreoffice')
 current=m.put('/synthetic-control/known-current',dict(schema='frw.Root.pptx-pdf-known-export-current.v1',operator='Root',source_only_accepted=True,source_directory=str(C),source_manifest=mr,kernel=binding['kernel'],toolchain=tools,whole_case_acceptance=False,original_effect_closed=True))
 intent=m.put('/synthetic-control/known-intent',dict(schema='frw.Root.pptx-pdf-export-once-intent.v1',operator='Root',state='INTENT_BEFORE_CGROUP_MOVE',consumed=False,operation_id='control-known',output='/synthetic-control/known-output',current=current,operation_clock=kclock,input={**known_input,'bytes':len(known),'mime':K['PPTX_MIME']},expectation=known_expectation,source_manifest=mr))
 reader=dict(source=binding['pdf_reader']['source'],helper=dict(path=K['PDFTOTEXT'],sha256=binding['pdf_reader']['executable']['sha256'],version=binding['pdf_reader']['version']),ocr_or_hosted_fallback=False)
 pdata=b'%PDF-in-memory-known-not-runtime-authority';pr=m.put('/synthetic-control/known-output/known.pdf',pdata);pa={**pr,'bytes':len(pdata)}
 pob=K['pdf_observation'](pdata,OLD['PAGE_TEXTS'],OLD['EXPECTED'],reader,pr['path']);por=m.put('/synthetic-control/known-output/EXPORTED-PDF-OBSERVATION.json',pob)
 ior=m.put('/synthetic-control/known-output/ORIGINAL-PPTX-STRUCTURAL.json',K['observe_pptx'](known))
 commands=[]
 for name in ('strace-version','office-version','pdftotext-version','export'):
  lr=m.put('/synthetic-control/known-output/'+name+'.log',b'inert log only')
  commands.append(dict(state='RETURNED_ZERO',exit_code=0,process_reaped=True,own_processes_zero=True,log={**lr,'bytes':14,'complete':True}))
 act=dict(schema='frw.Root.pptx-pdf-native-qualification-observation.v1',operator='Root',format='pptx',state='ACTUAL_KNOWN_PPTX_PDF_EXPORT_COMPLETE_ROOT_REVIEW_REQUIRED',own_processes_zero=True,temporary_homes_removed=True,whole_case_acceptance=False,full_format_acceptance=False,editable_preservation='FAIL_RETAINED',sources={n:sha((C/n).read_bytes()) for n in Q['SOURCES']},qualifier_source_sha256=sha((C/'qualify_pptx_pdf.py').read_bytes()),qualification_input=known_input,expectation=known_expectation,input_observation=ior,input_comparison=dict(status='MATCH'),phases=[dict(stage='export',qualified=True,input_unchanged=True,output_comparison=pob['comparison'],output_artifact=pa,output_observation=por)],commands=commands,started_monotonic=101.,ended_monotonic=150.,deadline_monotonic=179.,operation_clock=kclock,current=current,once_intent=intent,operation_id='control-known',**{n:binding[n]for n in ('consumer','strace','kernel','pdf_reader','source_manifest')})
 ar=m.put('/synthetic-control/known-output/OBSERVATION.json',act)
 qual=dict(schema='frw.Root.pptx-pdf-native-consumer-qualification.v1',operator='Root',format='pptx',export_filter=K['EXPORT_FILTER'],actual_observation=ar,full_format_acceptance=False,editable_preservation='FAIL_RETAINED',**{n:binding[n] for n in ('consumer','strace','kernel','pdf_reader','source_manifest','import_settings')})
 binding['consumer_qualification']=m.put('/synthetic-control/known-output/CONSUMER-QUALIFICATION.json',qual)
 # Genuine once-sent V02 producer+wire+native joins, all synthetic in memory.
 plan,run,receipt,wires=OLD['producer_values'](binding)
 for key,doc in wires.items():
  rr=m.put(key,doc)
  for name in ('source_update','getUpdates_wire','getFile_wire'):
   if receipt[name]['path']==key:receipt[name]={**rr,'bytes':len(enc(doc))}
  if receipt['companion_pdf']['getFile_wire']['path']==key:receipt['companion_pdf']['getFile_wire']={**rr,'bytes':len(enc(doc))}
 binding['ingress_receipt']=m.put('/synthetic-control/receipt',receipt);binding['run']=m.put('/synthetic-control/run',run);binding['plan']=m.put('/synthetic-control/plan',plan)
 origin,receiver,native=OLD['origin_values'](binding,receipt)
 origin['native_origin']=m.put('/offline/native',native);receiver['saved_origin']=origin['native_origin'];origin['receiver_reconciliation']=m.put('/offline/receiver',receiver)
 binding['origin_assessment']=m.put('/synthetic-control/origin',origin)
 # Source116 current record also satisfies the actual accepted V02 selector.
 source=m.put('/synthetic-control/source',dict(native_continuity=dict(source_identity='f'*64)))
 writer=m.put('/synthetic-control/writer',dict(schema='frw.Root.s07-sole-writer-authority.v1',operator='Root'))
 services=m.put('/synthetic-control/services',dict(inert=True));proof=m.put('/synthetic-control/nativeproof',dict(inert=True))
 tup=dict(installed=7,layers=0,native=0,source=116,project=116,service_owner='Root')
 tr=m.put('/synthetic-control/tuple',dict(schema='frw.Root.actual-installed-tuple.v1',tuple=tup,installed_source=source,permanent_services=services))
 callerpkg=json.loads((CALLER/'PACKAGE.json').read_bytes())
 installed=m.put('/synthetic-control/current116',dict(schema='frw.Root.ordinary-current116-bindings.v1',package=callerpkg['current_selection']['product_package'],actual_tuple=tr,installed_source=source,sole_writer=writer,fresh_native_proof=proof,permanent_services=services))
 ds=m.put('/synthetic-control/sourceaccepted',dict(source_only_accepted=True,source_directory=str(C),source_manifest=mr))
 resources=m.put('/synthetic-control/resources',dict(read_only=True,new_baseline_pause=False,decision='synthetic-control',local_affinity=[0,1]))
 binding['qualification']=m.put('/synthetic-control/genuine-closed',dict(inert=True))
 binding['current']=m.put('/synthetic-control/genuine-current',dict(schema='frw.Root.same-received-consumer-current.v1',operator='Root',actual_qualification=binding['qualification'],whole_case_acceptance=False,original_effect_closed=True,installed_source=installed,diagnostic_source=ds,local_resource_decision=resources))
 binding['operation_clock']=m.put('/synthetic-control/genuine-clock',dict(boot_id=binding['kernel']['boot_id'],origin_monotonic=200.,deadline_monotonic=320.))
 ap=ref(C/'v02_known_pdf_adapter.py',(C/'v02_known_pdf_adapter.py').read_bytes())
 accept=dict(schema='frw.Root.pptx-pdf-known-export-accepted.v1',operator='Root',accepted=True,qualification=binding['consumer_qualification'],actual_observation=ar,current_bindings=installed,source_manifest=mr,source_directory=str(C),adapter=ap,known_input=known_input,known_expectation=known_expectation,qualification_closed=True,own_processes_zero=True,temporary_homes_removed=True,original_effect_closed=True,runtime_or_semantic_acceptance=False,**{n:binding[n] for n in ('consumer','strace','pdf_reader','kernel')})
 acc=m.put('/synthetic-control/known-Root-acceptance',accept)
 pkg=copy.deepcopy(callerpkg);pkg.update(known_pdf_consumer=ap,known_pdf_qualification=binding['consumer_qualification'],known_pdf_acceptance=acc)
 value=dict(known_pdf_qualification=binding['consumer_qualification'],current_bindings=installed)
 return types.SimpleNamespace(m=m,binding=binding,qual=qual,act=act,pkg=pkg,value=value,current=current,intent=intent,known=known,genuine=genuine,expected=expected,pages=pages)

def bind_io(vm,m):return patch.dict(vm['correlate'].__globals__,dict(read_ref=m.read))
from contextlib import contextmanager
@contextmanager
def adapter_io(x):
 with patch.dict(A['BOUNDARY']['_check_known_qualification'].__globals__,dict(read_ref=x.m.read)), patch.dict(A['BOUNDARY'],dict(pinned_read=lambda *a,**k:b'inert-tool-only')):
  yield

def full_boundary():
 x=scenario()
 with bind_io(B,x.m):v=B['correlate'](x.binding)
 need(v['expectation']['source_only_fixture'] is False and len(v['additional_custody_refs'])>10)
 need(x.binding['received_artifact']['sha256']!=x.act['qualification_input']['sha256'])
 need(x.binding['expectation']['sha256']!=x.act['expectation']['sha256'])
control('full real pure B162 correlate accepts disjoint known and genuine hashes',full_boundary)

def boundary_bad(name,mutate,code):
 def f():
  x=scenario();mutate(x)
  with bind_io(B,x.m):reject(lambda:B['correlate'](x.binding),code)
 control(name,f)
boundary_bad('known fixture is rejected as genuine',lambda x:x.binding.update(received_artifact=x.act['qualification_input'],received_bytes=len(x.known),expectation=x.act['expectation']),'GENUINE_RECEIVED_EXPECTATION')
boundary_bad('genuine expectation cannot point to known SHA',lambda x:x.binding.update(expectation=x.act['expectation']),'EXPECTATION_INPUT_SHA')
def mutate_known(x,key,val):
 ar=x.qual['actual_observation'];new=x.m.replace(ar,lambda a:a.__setitem__(key,val));x.qual['actual_observation']=new;x.binding['consumer_qualification']=x.m.put('/synthetic-control/changedqual',x.qual)
boundary_bad('known qualification input cannot be genuine',lambda x:mutate_known(x,'qualification_input',x.binding['received_artifact']),'KNOWN_PDF_INPUT_EXPECTATION')
boundary_bad('known expectation cannot be genuine',lambda x:mutate_known(x,'expectation',x.binding['expectation']),'KNOWN_PDF_INPUT_EXPECTATION')
boundary_bad('known stale source SHA fails',lambda x:mutate_known(x,'qualifier_source_sha256','0'*64),'SOURCE_GRAPH')
boundary_bad('known unreaped process fails',lambda x:mutate_known(x,'own_processes_zero',False),'COMPLETE_ACTUAL')
boundary_bad('known cleanup failure fails',lambda x:mutate_known(x,'temporary_homes_removed',False),'COMPLETE_ACTUAL')
boundary_bad('known incomplete command log fails',lambda x:mutate_known(x,'commands',[dict(c,log=dict(c['log'],complete=False))for c in x.act['commands']]),'COMMANDS')
boundary_bad('known source clock cannot escape original window',lambda x:mutate_known(x,'deadline_monotonic',181.),'KNOWN_CLOCK')
boundary_bad('known signed current cannot bind other source',lambda x:mutate_known(x,'current',x.binding['current']),'KNOWN_CURRENT')
boundary_bad('missing actual companion rejects',lambda x:x.binding.update(delivered_pdf={'path':'/none','sha256':'0'*64}),'COMPANION_PDF')
boundary_bad('changed genuine source bytes rejects',lambda x:x.binding['received_artifact'].update(sha256='0'*64),'EXPECTATION_INPUT_SHA')
boundary_bad('wrong actual operation boot rejects',lambda x:x.binding['kernel'].update(boot_id='wrong'),'QUALIFICATION_JOIN')

def adapter_positive():
 x=scenario()
 with adapter_io(x):need(A['validate'](x.m,x.pkg,x.value) is True)
control('actual adapter ABI returns literal True after full known-only join',adapter_positive)
for key,val in [('accepted',False),('qualification_closed',False),('runtime_or_semantic_acceptance',True),('current_bindings',{'path':'/wrong','sha256':'0'*64}),('source_directory','/wrong')]:
 def f(key=key,val=val):
  x=scenario();r=x.pkg['known_pdf_acceptance'];x.pkg['known_pdf_acceptance']=x.m.replace(r,lambda a:a.__setitem__(key,val))
  with adapter_io(x):reject(lambda:A['validate'](x.m,x.pkg,x.value))
 control('adapter rejects Root acceptance '+key,f)
def missing_accept():
 x=scenario();x.pkg.pop('known_pdf_acceptance')
 with adapter_io(x):reject(lambda:A['validate'](x.m,x.pkg,x.value),'ACCEPTANCE_REF')
control('raw certificate alone cannot grant Root acceptance',missing_accept)
def mismatched_ref():
 x=scenario();x.value['known_pdf_qualification']={'path':'/sibling','sha256':'0'*64}
 with adapter_io(x):reject(lambda:A['validate'](x.m,x.pkg,x.value),'REFERENCE')
control('V02 input qualification reference equality rejects sibling',mismatched_ref)

def check_actual():
 x=scenario();utility=runpy.run_path(str(D/'base/qualify_office.py'));plan=OLD['make_plan'](x.binding['source_manifest'])
 now=time.monotonic();plan['kernel']=x.binding['kernel'];plan['operation_clock']=dict(boot_id=x.binding['kernel']['boot_id'],origin_monotonic=now-1,deadline_monotonic=now+60)
 plan['toolchain']['consumer']['executable']['sha256']=utility['PINS'][K['ENGINE']];plan['toolchain']['strace']['executable']['sha256']=utility['PINS'][K['STRACE']];plan['toolchain']['wrapper']['sha256']=utility['PINS'][utility['WRAPPER']]
 Q['check_actual'](plan,utility)
 for mutate,code in [(lambda p:p['kernel'].update(boot_id='stale'),'KERNEL_BOOT'),(lambda p:p['operation_clock'].update(origin_monotonic=now+1),'CLOCK'),(lambda p:p['operation_clock'].update(deadline_monotonic=now),'CLOCK'),(lambda p:p['toolchain']['consumer']['executable'].update(sha256='0'*64),'TOOL_DECLARATION'),(lambda p:p['toolchain']['strace']['executable'].update(sha256='0'*64),'TOOL_DECLARATION'),(lambda p:p['toolchain']['wrapper'].update(sha256='0'*64),'WRAPPER_DECLARATION'),(lambda p:p['toolchain']['pdf_reader']['source'].update(path='/wrong'),'READER_SOURCE')]:
  bad=copy.deepcopy(plan);mutate(bad);reject(lambda:Q['check_actual'](bad,utility),code)
control('qualifier actual boot clock tool wrapper reader admission and negatives',check_actual)

def source_oracle():
 x=scenario();K['validate_source_expectation'](x.known,OLD['EXPECTED']);K['validate_source_expectation'](x.genuine,x.expected)
 bad=copy.deepcopy(x.expected);bad['chart_label_source']['values'][0]='999.25';bad['pages'][0]['chart_numeric_labels'][0]='999.25';bad['pages'][0]['text_tokens']=[p.replace('2718.25','999.25')for p in bad['pages'][0]['text_tokens']]
 reject(lambda:K['validate_source_expectation'](x.genuine,bad))
 for token in ('2718.25','314.75'):
  pages=copy.deepcopy(OLD['PAGE_TEXTS']);pages[0]=pages[0].replace(token,'');need(K['compare_pdf_pages'](pages,OLD['EXPECTED'])['status']=='DIFFERENT')
control('source chart showVal 2718.25/314.75 distinct table 3601.50/1499.70 and false chart oracle',source_oracle)

def binder_and_full_caller():
 x=scenario();binder=runpy.run_path(str(D/'v02-seam/bind_source.py'));pkg=binder['bind'](x.pkg,frontier_descriptor=x.m.put('/synthetic-control/frontier',{}),known_pdf_consumer=x.pkg['known_pdf_consumer'],known_pdf_qualification=x.pkg['known_pdf_qualification'],known_pdf_acceptance=x.pkg['known_pdf_acceptance'],read=x.m.read)
 need(pkg['known_pdf_acceptance']==x.pkg['known_pdf_acceptance'])
 root=runpy.run_path(str(CALLER/'source/root_v02.py'));builder=runpy.run_path(str(CALLER/'source/build_inputs.py'))
 fields={n:x.m.put('/synthetic-control/input-'+n,{})for n in builder['FIELDS']-{'cursor_sha256','input_stat'}};fields.update(x.value,cursor_sha256='a'*64,input_stat=dict(device=1,inode=1,size_bytes=5660,uid=1000,mtime_ns=1,ctime_ns=1),predecessor_closure=pkg['future_frontier']['closure'])
 value=builder['build'](**fields);canonical=pkg['canonical_consumer'];package_ref=x.m.put('/synthetic-control/bound-v02-package',pkg)
 sourceaccept=dict(schema='frw.Root.v02-source-review-accepted.v1',operator='Root',accepted=True,source_only=True,package=package_ref,canonical_consumer=canonical,final_source=pkg['future_consumer_source'],strict_guard_unchanged=True,runtime_or_semantic_acceptance=False)
 value['consumer_source_acceptance']=x.m.put('/synthetic-control/input-consumer_source_acceptance',sourceaccept)
 tq=dict(schema='frw.Root.v02-actual-tester-qualified.v1',operator='Root',accepted=True,canonical_consumer=canonical,current_bindings=value['current_bindings'],final_source=pkg['future_consumer_source'],source_identity='f'*64,installed=True,fresh_selected_process=True,actual_native_counterparts_checked=True,runtime_or_semantic_acceptance=False)
 value['tester_qualification']=x.m.put('/synthetic-control/input-tester_qualification',tq)
 pr=dict(schema='frw.Root.v02-priority-boundary-accepted.v1',operator='Root',accepted=True,case='V-02',current_bindings=value['current_bindings'],predecessor_closure=value['predecessor_closure'],baseline_boundary=value['baseline_boundary'],sole_Root_integrator=True,higher_priority_effects_settled=True,new_independent_effect_only=True,old_replay_authorized=False,observed_monotonic=time.monotonic())
 value['priority_authority']=x.m.put('/synthetic-control/input-priority_authority',pr)
 history=dict(schema='frw.Root.v02-original-once-contamination-review.v1',operator='Root',accepted=True,case='V-02',input_sha256=pkg['original_fixture']['sha256'],original_request=pkg['original_request'],current_bindings=value['current_bindings'],predecessor_closure=value['predecessor_closure'],actual_history_and_original_once_checked=True,original_V02_not_already_admitted_or_sent=True,earlier_presentation_read_or_equivalent_truth_checked=True,known_contamination_explicitly_considered=True,all_prior_case_effects_and_closed_clocks_preserved=True,no_freshness_inferred_from_hash_or_rename=True,new_original_case_admission_authorized=True)
 value['once_history_contamination_review']=x.m.put('/synthetic-control/input-once_history_contamination_review',history)
 # No caller logic is stubbed. Only protected reads and fixed tool hash reads
 # are replaced with the in-memory model; the real adapter is loaded by caller.
 real_load=root['load'];seen=[]
 def load(r,n):
  mod=real_load(r,n)
  if n=='_v02_final_known_pdf_consumer':
   mod.BOUNDARY['_check_known_qualification'].__globals__['read_ref']=x.m.read
   mod.BOUNDARY['pinned_read']=lambda *a,**kw:b'inert-tool-only';seen.append(n)
  return mod
 with patch.dict(root['check_inputs'].__globals__,dict(load=load)):
  need(root['check_inputs'](x.m,pkg,package_ref,value,types.SimpleNamespace(T=Path(canonical['path'])))==canonical)
 need(seen==['_v02_final_known_pdf_consumer'])
control('own binder accepted ref reaches genuine frozen V02 check_inputs and real adapter whole positive',binder_and_full_caller)

# Source-only reader checks use injected inert process APIs. No child is started.
def reader_caps():
 runner=P['_BoundedLocalRunner'](b'x',time.monotonic()+1)
 reject(lambda:runner.run(['/bin/sh','x','-'],capture_output=True,timeout=1),'FIXED_READER_ARGV')
 # Exact source/reader path check is meaningful before tool execution.
 reject(lambda:P['read_pages'](b'%PDF-memory-only',D/'fixtures/known-visible-label.pptx'),'CUSTODY')
 need('read_end = time.monotonic() + 45' in (C/'pptx_pdf_observation.py').read_text())
 need("binding, read_end, page_reader)" in (C/'pptx_pdf_observation.py').read_text())
control('bounded reader fixed argv/source custody and separate retained-read clock',reader_caps)

def qualifier_records():
 x=scenario();plan=OLD['make_plan'](x.binding['source_manifest']);plan.update(current=x.current,once_intent=x.intent,operation_id='control-known',output='/synthetic-control/known-output',operation_clock=x.act['operation_clock'],kernel=x.binding['kernel'])
 plan['toolchain']=x.m.document(x.current)['toolchain']
 with patch.dict(Q['_check_plan_records'].__globals__,dict(read_ref=x.m.read)):
  Q['_check_plan_records'](plan)
  for name,key,val,code in [('current','source_directory','/wrong','CURRENT_EXACT'),('current','source_only_accepted',False,'CURRENT_EXACT'),('once_intent','consumed',True,'ONCE_INTENT'),('once_intent','operation_clock',dict(plan['operation_clock'],deadline_monotonic=179.),'CAS_JOIN')]:
   saved=copy.deepcopy(x.m.raw)
   bad=copy.deepcopy(plan);bad[name]=x.m.replace(plan[name],lambda r:r.__setitem__(key,val))
   reject(lambda:Q['_check_plan_records'](bad),code)
   x.m.raw=saved
control('known current source/tool and exact once-plan CAS admission positive and negatives',qualifier_records)

def observation_setup(x,extra=''):
 root='/synthetic-control/runtime';inp='/mnt/input/received.pptx';out='/tmp/friday-office-control/out/received.pdf'
 trace=('1 200.100 execve("/opt/friday-document-toolchain/root/usr/lib/libreoffice/program/soffice", ["soffice"], 0x0) = 0\n'
        '1 200.200 execve("/opt/friday-document-toolchain/root/usr/lib/libreoffice/program/soffice.bin", ["soffice.bin"], 0x0) = 0\n'
        f'1 200.300 openat(AT_FDCWD, "{inp}", O_RDONLY) = 3\n'
        f'1 200.400 write(4<{out}>, "inert", 5) = 5\n'+extra+'1 200.900 +++ exited with 0 +++\n').encode()
 tr=x.m.put(root+'/EXPORT-SYSCALLS-PRIVATE.log',trace);lr=x.m.put(root+'/EXPORT-CONSUMER-PRIVATE.log',b'inert')
 orig=x.m.put(root+'/ORIGINAL-PPTX-STRUCTURAL.json',K['observe_pptx'](x.genuine))
 data=b'%PDF-in-memory-exported-genuine-not-authority';r=x.m.put(root+'/received-exported.pdf',data);art={**r,'bytes':len(data)}
 reader=dict(source=x.binding['pdf_reader']['source'],helper=dict(path=K['PDFTOTEXT'],sha256=x.binding['pdf_reader']['executable']['sha256'],version=x.binding['pdf_reader']['version']),ocr_or_hosted_fallback=False)
 expo=K['pdf_observation'](data,x.pages,x.expected,reader,r['path']);er=x.m.put(root+'/EXPORTED-PDF-OBSERVATION.json',expo)
 dd=x.m.read(x.binding['delivered_pdf']);delivered=K['pdf_observation'](dd,x.pages,x.expected,reader,x.binding['delivered_pdf']['path']);dr=x.m.put(root+'/DELIVERED-PDF-OBSERVATION.json',delivered)
 phase=dict(stage='export',trace_filter=O['FILTER'],trace_complete=True,exit_code=0,process_reaped=True,input_unchanged=True,timed_out=False,overflow=False,started_monotonic=201.,ended_monotonic=215.,deadline_monotonic=235.,output_artifact=art,input_sha256=x.binding['received_artifact']['sha256'],input_path=inp,output_path=out,trace_reference=tr,trace_bytes=len(trace),log_reference=lr,input_observation=orig,output_observation=er,output_comparison=expo['comparison'])
 br=x.m.put(root+'/binding',x.binding)
 worker=dict(schema='frw.Root.pptx-pdf-finite-native-consumer-draft.v1',state=O['COMPLETE'],binding_sha256=br['sha256'],invocation_id=x.binding['invocation_id'],received_sha256=x.binding['received_artifact']['sha256'],delivered_pdf_sha256=x.binding['delivered_pdf']['sha256'],received_snapshot_unchanged=True,delivered_snapshot_unchanged=True,process_reaped=True,format='pptx',phases=[phase],delivered_observation=dr,delivered_comparison=delivered['comparison'])
 host=dict(schema='frw.Root.pptx-pdf-export-existing-boundary-host-report.v1',state=O['COMPLETE'],own_processes_zero=True,original_received_preserved=True,delivered_pdf_preserved=True,worker_exit_code=0,worker_report=worker)
 hr=x.m.put(root+'/HOST-OBSERVER-RESULT.json',host);facts=O['trace_facts'](trace,inp,out)
 rev=dict(schema='frw.Root.pptx-pdf-actual-invocation-review.v1',operator='Root',binding=br,host_report=hr,invocation_id=x.binding['invocation_id'],trace_filter=O['FILTER'],phase_reviews=[dict(stage='export',trace_reference=tr,exec_records=facts['exec_records'],network_records=facts['network_records'],decision='FIXED_PPTX_PDF_EXPORT_GRAPH_NO_NETWORK_OR_COMMAND_INITIATION')])
 rr=x.m.put(root+'/review',rev)
 return br,hr,rr
@contextmanager
def observation_io(x):
 with patch.dict(O['authenticate'].__globals__,dict(read_ref=x.m.read)), patch.dict(O['BOUNDARY']['correlate'].__globals__,dict(read_ref=x.m.read)):
  yield

def full_observation():
 x=scenario();args=observation_setup(x);seen=[]
 def pages(data,path,end,binding):
  need(end>time.monotonic() and end<=time.monotonic()+45);seen.append((path,sha(data)));return dict(pages=x.pages)
 with observation_io(x):result=O['authenticate'](*args,page_reader=pages)
 need(result['bounded_projection_status']=='MATCH' and len(seen)==2 and seen[0][1]!=seen[1][1])
 need(result['full_format_acceptance'] is False and result['editable_preservation']=='FAIL_RETAINED')
control('full nearest observation consumer + real trace parser + distinct known/genuine/exported/delivered hashes',full_observation)
for name,extra,reason in [('network','1 200.500 socket(AF_INET, SOCK_STREAM, 0) = 6\n','NETWORK_FAMILY_INITIATION_OBSERVED'),('unintended exec','1 200.500 execve("/bin/sh", ["sh", "-c", "inert"], 0x0) = 0\n','UNEXPECTED_EXEC_GRAPH')]:
 def f(extra=extra,reason=reason):
  x=scenario();args=observation_setup(x,extra)
  with observation_io(x):res=O['authenticate'](*args,page_reader=lambda *a:dict(pages=x.pages))
  need(res['status']=='FAIL' and res['reason']==reason)
 control('actual observation rejects '+name+' even with matching Root review label',f)
for key,val,code in [('trace_complete',False,'COMPLETE_ACTUAL'),('input_sha256','0'*64,'LINEAGE_JOIN'),('ended_monotonic',240.,'WINDOW_REQUIRED')]:
 def f(key=key,val=val,code=code):
  x=scenario();br,hr,rr=observation_setup(x);h=x.m.document(hr);h['worker_report']['phases'][0][key]=val;hr2=x.m.put(hr['path'],h);r=x.m.document(rr);r['host_report']=hr2;rr=x.m.put(rr['path'],r)
  with observation_io(x):reject(lambda:O['authenticate'](br,hr2,rr,page_reader=lambda *a:dict(pages=x.pages)),code)
 control('actual observation rejects changed '+key,f)

def bounded_runner_cases():
 import collections
 data=(D/'fixtures/known-visible-label.pptx').read_bytes();path=D/'fixtures/known-visible-label.pptx'
 for payload,wanted,exitcode,expired in [(b'alpha\fbravo\f',None,0,False),(b'x'*1_000_001,'STREAM_CAP',0,False),(b'\xff','',0,False),(b'inert','NONZERO',1,False),(b'inert','DEADLINE',0,True)]:
  queues={101:collections.deque(payload[i:i+65536]for i in range(0,len(payload),65536)),102:collections.deque()};waits=[];calls=[]
  class Pipe:
   def __init__(self,fd):self.fd=fd
   def fileno(self):return self.fd
   def close(self):pass
  proc=types.SimpleNamespace(stdout=Pipe(101),stderr=Pipe(102),returncode=exitcode,pid=123456789,poll=lambda:exitcode,wait=lambda **kw:waits.append(kw)or exitcode)
  class Selector:
   def __init__(self):self.reg={}
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def register(self,pipe,event,name):self.reg[pipe.fileno()]=types.SimpleNamespace(fileobj=pipe,data=name)
   def unregister(self,pipe):self.reg.pop(pipe.fileno())
   def get_map(self):return self.reg
   def select(self,timeout):return [(v,1)for v in list(self.reg.values())]
  def read(fd,cap):return queues[fd].popleft()if queues[fd]else b''
  runner=P['_BoundedLocalRunner'](data,time.monotonic()+(-1 if expired else 10))
  with patch.object(P['subprocess'],'Popen',side_effect=lambda argv,**kw:calls.append(argv)or proc),patch.object(P['selectors'],'DefaultSelector',Selector),patch.object(P['os'],'set_blocking',lambda *args:None),patch.object(P['os'],'read',read):
   fn=lambda:runner.run(['pdftotext',str(path),'-'],capture_output=True,timeout=5)
   if wanted is None:need(fn().stdout==payload)
   else:reject(fn,wanted or None)
  need(len(calls)==1 and calls[0][0]=='/usr/bin/pdftotext' and len(waits)>=1)
control('bounded reader positive plus real stream-cap invalid-UTF8 nonzero deadline cleanup branches with inert process double',bounded_runner_cases)

def adapter_cas():
 x=scenario();base_read=x.m.read;target=x.pkg['known_pdf_qualification']['path'];reads=[]
 def changed(ref,*args,**kwargs):
  data=base_read(ref,*args,**kwargs)
  if ref['path']==target:
   reads.append(ref)
   if len(reads)==1:x.m.raw[target]=data+b' '
  return data
 x.m.read=changed
 with adapter_io(x):reject(lambda:A['validate'](x.m,x.pkg,x.value),'SYNTHETIC_PIN')
control('adapter CAS rejects qualification changed after first document read',adapter_cas)
def frozen_caller_pins():
 pkg=json.loads((CALLER/'PACKAGE.json').read_bytes())
 for n in ('root_v02.py','build_inputs.py','v02_frontier.py'):
  r=pkg['files'][n];need(sha(Path(r['path']).read_bytes())==r['sha256'])
 need('set(pkg)' not in (CALLER/'source/root_v02.py').read_text())
 need('known_pdf_acceptance' in (D/'v02-seam/bind_source.py').read_text())
control('actual frozen V02 caller/builder/frontier pins unchanged and new binder key survives real consumer',frozen_caller_pins)

def exact_v02_only():
 for change in ('request','input_sha','source_reference','output'):
  x=scenario();p=x.m.document(x.binding['plan']);r=x.m.document(x.binding['run'])
  if change=='request':p['new_task']['request']='V01 read this presentation'
  elif change=='input_sha':p['new_scenario']['steps'][0]['input']['sha256']='0'*64;r['scenario']=p['new_scenario']
  elif change=='source_reference':p['new_task']['source_reference']={'run_id':'old'}
  else:p['new_task']['output'][0]['filename']='forced.pptx'
  x.binding['plan']=x.m.put(x.binding['plan']['path'],p);x.binding['run']=x.m.put(x.binding['run']['path'],r)
  with bind_io(B,x.m):reject(lambda:B['correlate'](x.binding),'EXACT_GENUINE_V02')
control('V01 question wrong table input retained source or constrained output cannot substitute genuine V02',exact_v02_only)

result=dict(schema='frw.Root.b162.whole-pure-review-controls.v1',total=len(RESULT),passed=sum(r['status']=='PASS'for r in RESULT),failed=sum(r['status']=='FAIL'for r in RESULT),controls=RESULT,all_authorities_and_PDF_bytes_in_memory_synthetic=True,actual_PDF_files_created=0,actual_helpers_started=0,actual_effects=[])
path=D/'controls/REVIEW-RESULT.json';path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');path.chmod(0o600)
print(json.dumps({k:result[k]for k in ('total','passed','failed')}));raise SystemExit(bool(result['failed']))
