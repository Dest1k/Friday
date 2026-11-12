"""Real ingress/custody functions, owned synthetic nested large source refs only."""
import hashlib,json,os,re,resource,socket,subprocess,sys,types
from pathlib import Path
R=Path(__file__).resolve().parent;B=R.parent
W=Path('/home/jericho/.cache/FRW-SOL-V3-F06-SAME-UPLOAD-WRONG-EDIT-SOURCE-20261112/protocol-stand')
os.umask(0o077);resource.setrlimit(resource.RLIMIT_CPU,(90,90));resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,768*1024**2))
def sha(b):return hashlib.sha256(b).hexdigest()
def encoded(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def load(p):
 m=types.ModuleType('SYNTHETIC_NESTED_'+p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def rf(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=sha(b))
CHECKS=[];COVERAGE=[];CASES=[]
def good(n,c=True):assert c,n;CHECKS.append(n)
def refused(n,fn,text=None):
 try:fn()
 except Exception as exc:
  assert text is None or text in str(exc),(n,type(exc).__name__,str(exc));CHECKS.append(n);return
 raise AssertionError(n+':did not refuse')
# Only trusted inert source and compact fixture templates are read before audit.
fixture_raw=(W/'first_fixture.py').read_text();control_raw=(W/'control.py').read_text()
wrong_extension=control_raw[control_raw.index("principal=first['B'];rid='SYNTHETIC-correct-read-closed';sr=c['source_reference']"):control_raw.index('# Bind only private synthetic source descriptors')]
for branch in ('correct','wrong-edit'):
 CASE=R/'nested-checks'/branch;CASE.mkdir(mode=0o700,parents=True)
 own=R/'candidate'/branch
 F=load(own/'first_ingress.py');A=load(R/'candidate/correct/f06_source.py');A.SOURCE=dict(A.SOURCE,path=str(CASE/'SYNTHETIC-retained-descriptor-NEVER-OPENED.docx'))
 F.STATE=CASE/'SYNTHETIC-STATE';F.STATE.mkdir(mode=0o700);(F.STATE/'runs').mkdir(mode=0o700)
 closed_first_clock_ref=dict(path=str(CASE/'SYNTHETIC-old-first-clock-NEVER-READ.json'),bytes=123,sha256='e'*64)
 closed_correct_clock_ref=dict(path=str(CASE/'SYNTHETIC-old-correct-clock-NEVER-READ.json'),bytes=124,sha256='f'*64)
 first_raw=fixture_raw.replace("'/SYNTHETIC-T28-ONLY/'+name","str(CASE/'first-fixture'/name)")
 first_raw=first_raw.replace("b'#SYNTHETIC-NO-ACTUAL-CONSUMER'","b'#SYNTHETIC-NO-ACTUAL-CONSUMER\\n'+b'S'*1250000")
 first_raw=first_raw.replace('authority=dummy,boundary=',"authority=dummy,resources={'clock':CLOSED_FIRST_CLOCK_REF},boundary=")
 ns=dict(A=A,F=F,C=own,code={str(own/'first_ingress.py'):(own/'first_ingress.py').read_bytes()},json=json,CASE=CASE,CLOSED_FIRST_CLOCK_REF=closed_first_clock_ref)
 exec(compile(first_raw,str(CASE/'SYNTHETIC-first-fixture-generator.py'),'exec'),ns)
 c,scenario,first,_,data=ns['fixture']()
 def put(name,value,raw=False):
  p=Path(name);p=p if p.is_absolute() else CASE/p;assert p.is_relative_to(CASE)
  p.parent.mkdir(parents=True,exist_ok=True,mode=0o700);p.write_bytes(value if raw else encoded(value));p.chmod(0o600);return rf(p)
 for path,raw in data.items():
  p=Path(path)
  if p.is_relative_to(own):assert p.read_bytes()==raw
  else:put(p,raw,True)
 m=load(R/'checks'/branch/'SYNTHETIC-full-consumer.py')
 # No Path/proc remap is needed: these real leaf functions touch only explicit refs.
 original=load(B/'checks'/branch/'SYNTHETIC-full-consumer.py')
 first_binding=json.loads(Path(first['first_binding']['path']).read_bytes());first_source=first_binding['source'];assert first_source['bytes']>1048576
 callfirst=lambda:F.validate(c,m._f06_reference_read)
 if branch=='wrong-edit':
  A=load(own/'f06_source.py');A.SOURCE=dict(A.SOURCE,path=str(CASE/'SYNTHETIC-retained-descriptor-NEVER-OPENED.docx'))
  fake_source=A.SOURCE;M=types.SimpleNamespace(STATE=F.STATE);CONTROL='positive';dummy=put('SYNTHETIC-proof-basis.json',{'SYNTHETIC_ONLY':True})
  # Reuse the existing compact pure correct-read fixture construction only.
  # The old bound consumer source is deliberately >1MiB and never executed.
  extension=wrong_extension.replace("b'# SYNTHETIC closed source metadata; never imported\\n'","b'# SYNTHETIC closed source metadata; never imported\\n'+b'C'*1500000")
  scope=dict(Path=Path,A=A,F=F,M=M,CASE=CASE,CONTROL=CONTROL,first=first,c=c,dummy=dummy,put=put,sha=sha,encoded=encoded,fake_source=fake_source,closed_first_clock_ref=closed_first_clock_ref,closed_correct_clock_ref=closed_correct_clock_ref)
  exec(compile(extension,str(CASE/'SYNTHETIC-correct-fixture-generator.py'),'exec'),scope)
  c=scope['c'];correct=scope['correct'];c['resources']=dict(c['resources'],clock=put('SYNTHETIC-future-clock.json',{'started_at':483}))
  cb=json.loads(Path(correct['correct_binding']['path']).read_bytes());correct_source=cb['source'];assert correct_source['bytes']>1048576
  callcorrect=lambda:F.correct_read(c,m._f06_reference_read,first)
 else:correct_source=None;callcorrect=None
 CASES.append(dict(branch=branch,F=F,m=m,old=original,c=c,first=first,first_source=first_source,correct_source=correct_source,callfirst=callfirst,callcorrect=callcorrect))
 COVERAGE.append(dict(branch=branch,first='real complete first_ingress.validate -> doc(first_binding) -> real original_custody -> readref(binding[source])',correct='real complete wrong-edit first_ingress.correct_read -> doc(correct_binding) -> readref(binding[source])' if branch=='wrong-edit' else None,first_source_bytes=first_source['bytes'],correct_source_bytes=correct_source['bytes'] if correct_source else None,all_evidence='owned synthetic files only; no actual first/correct upload or semantic acceptance'))
# Freeze bindings of closures above before iterating; no dynamic last-case aliases.
for x in CASES:
 x['callfirst']=(lambda q=x:q['F'].validate(q['c'],q['m']._f06_reference_read))
 if x['branch']=='wrong-edit':x['callcorrect']=(lambda q=x:q['F'].correct_read(q['c'],q['m']._f06_reference_read,q['first']))
AUDIT={'own_opens':0,'blocked':[]}
def audit(event,args):
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  if not p.is_relative_to(R):AUDIT['blocked'].append(str(p));raise PermissionError('NESTED_UNOWNED_OPEN_REFUSED')
  AUDIT['own_opens']+=1
 elif event.startswith(('socket.','subprocess.','os.exec','os.spawn','os.fork')):raise PermissionError('NESTED_EXTERNAL_EFFECT_REFUSED')
 elif event in ('os.scandir','os.listdir') and not Path(args[0]).is_relative_to(R):raise PermissionError('NESTED_UNOWNED_DIRECTORY_REFUSED')
sys.addaudithook(audit)
for x in CASES:
 branch,F,m,c,first=x['branch'],x['F'],x['m'],x['c'],x['first']
 good(branch+':real_complete_first_ingress_nested_source_gt1MiB',x['callfirst']()==first)
 if x['callcorrect']:good(branch+':real_complete_correct_read_nested_linked_source_gt1MiB',x['callcorrect']()['status']=='ROOT_BOUND_CORRECT_READ_ACCEPTED')
 refused(branch+':R1_nested_first_bound_source_gap_reproduced',lambda:F.validate(c,x['old']._f06_reference_read),'Unsafe file type, link count, or size')
 def root_read(path,*,private=True):return m.safe_read(path,limit=24*1024**2,private=private)
 good(branch+':Root_path_reader_ABI_no_callback_full_nested_first',F.validate(c,root_read)==first)
 if x['callcorrect']:good(branch+':Root_path_reader_ABI_no_callback_full_nested_correct',F.correct_read(c,root_read,first)['status']=='ROOT_BOUND_CORRECT_READ_ACCEPTED')
 for name,r,full in [('first_binding.source',x['first_source'],x['callfirst'])]+([('correct_binding.source',x['correct_source'],x['callcorrect'])] if x['correct_source'] else []):
  p=Path(r['path']);raw=p.read_bytes()
  good(branch+':'+name+':actual_ingress_readref_positive',F.readref(r,m._f06_reference_read)==raw)
  refused(branch+':'+name+':direct_path_stays1MiB',lambda:m._f06_reference_read(p),'Unsafe file type, link count, or size')
  for label,b,mode in [('same_size_wrong_hash',b'X'+raw[1:],0o600),('actual_oversize',raw+b'X',0o600),('private0640',raw,0o640)]:
   p.write_bytes(b);p.chmod(mode);refused(branch+':'+name+':full_ingress_'+label,full)
  p.write_bytes(raw);p.chmod(0o600)
  for label,bounds in [('declared_too_small',dict(r,bytes=len(raw)-1)),('declared_too_large',dict(r,bytes=len(raw)+1)),('declared_over24MiB',dict(r,bytes=24*1024**2+1)),('declared_bool',dict(r,bytes=True)),('declared_wrong_sha',dict(r,sha256='0'*64)),('path_alias',dict(r,path=str(p.parent)+'/./'+p.name))]:
   refused(branch+':'+name+':leaf_'+label,lambda z=bounds:F.readref(z,m._f06_reference_read))
  link=p.with_name('SYNTHETIC-hardlink-'+p.name);os.link(p,link);refused(branch+':'+name+':full_ingress_hardlink',full);link.unlink()
  alias=p.with_name('SYNTHETIC-symlink-'+p.name);alias.symlink_to(p);refused(branch+':'+name+':leaf_symlink',lambda:F.readref(dict(r,path=str(alias)),m._f06_reference_read),'Symlink path refused');alias.unlink()
  invalid=lambda path:raw;invalid.f06_read_reference=False
  refused(branch+':'+name+':bad_callback_type',lambda:F.readref(r,invalid),'F06_FIRST_BOUNDED_REFERENCE_CALLBACK_REQUIRED')
  invalid.f06_read_reference=None
  refused(branch+':'+name+':present_None_callback_refused',lambda:F.readref(r,invalid),'F06_FIRST_BOUNDED_REFERENCE_CALLBACK_REQUIRED')
  liar=lambda path:raw;liar.f06_read_reference=lambda rr:b'X'*rr['bytes']
  refused(branch+':'+name+':callback_result_still_revalidated',lambda:F.readref(r,liar),'F06_FIRST_REF_CHANGED')
  good(branch+':'+name+':same_original_files_valid_after_negatives',full() is not None)
refused('confinement_external_open',lambda:open('/etc/hostname','rb'),'NESTED_UNOWNED_OPEN_REFUSED')
refused('confinement_network',lambda:socket.socket(),'NESTED_EXTERNAL_EFFECT_REFUSED')
result=dict(status='PASS',revision=2,count=len(CHECKS),checks=CHECKS,coverage=COVERAGE,audit=AUDIT,source_scope='real2 ingress implementations and full original_custody/correct_read functions; only STATE/source descriptor constants synthetic',actual_ordinary_or_semantic_privacy_formal_F06='NOT_RUN_NOT_ACCEPTED',actual_first_correct_or_wrongedit_effect=False,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
p=R/'NESTED-QUALIFICATION-RESULT.json';p.write_bytes(encoded(result));p.chmod(0o600);print(json.dumps({'status':'PASS','count':len(CHECKS),'result':rf(p)},sort_keys=True))
