"""Future Root source-pinned current208 default spec/inspect on real managed H.
Import is inert. Retained genuine private497 scripts are the source consumer;
managed H supplies installed state. Raw H scripts need not be raw source images.
Prospective209 real-H spec belongs to the unchanged builder/candidate499 path.
"""
from pathlib import Path
import errno,hashlib,importlib.util,json,os,resource,sys
B=Path(__file__).parent
RECORD_SCHEMA='frw.root209.source-pinned-current-default-preflight.v2'
PASS_STATE='PASS_SOURCE_PINNED_CURRENT208_DEFAULT_SPEC_INSPECT_ON_REAL_H_NOT_ADMISSION'
REFUSED_STATE='REFUSED_SOURCE_PINNED_CURRENT208_PREFLIGHT_NOT_ADMISSION'
FIXED_CODES={'READONLY_CONSUMER_FILESYSTEM_MUTATION_DENIED','READONLY_CONSUMER_HARD_EFFECT_DENIED','SOURCE_PINNED_CURRENT208_PREFLIGHT_FAILED','SOURCE_PINNED_CURRENT208_PREFLIGHT_COMPLETED'}

def trace_locations(tb):
 rows=[]
 while tb is not None and len(rows)<64:
  code=tb.tb_frame.f_code;rows.append(dict(file=code.co_filename,function=code.co_name,line=tb.tb_lineno));tb=tb.tb_next
 return rows

def correlate_completed(returncode,stdout,stderr):
 """Pure parsing AFTER capture. Warning/malformed lines never lose the child exitcode."""
 if type(returncode)is not int:raise ValueError('captured_integer_exitcode_required')
 records=[];other=0;malformed=0
 for stream,output in [('stdout',stdout),('stderr',stderr)]:
  if not isinstance(output,str)or len(output)>16*1024**2:
   malformed+=1;continue
  for line in output.splitlines():
   if not line.strip():continue
   try:v=json.loads(line)
   except (ValueError,TypeError):other+=1;continue
   if not isinstance(v,dict)or v.get('schema')!=RECORD_SCHEMA:other+=1;continue
   if not isinstance(v.get('state'),str)or not isinstance(v.get('fixed_code'),str)or v['state']not in {PASS_STATE,REFUSED_STATE}or v['fixed_code']not in FIXED_CODES:malformed+=1;continue
   safe={k:v[k]for k in ('schema','state','phase','exception_class','fixed_code','private_exception_message_emitted')if k in v}
   if not isinstance(safe.get('phase'),str)or safe['phase']not in {'source_ref_validation','unmodified_source497_default_spec_inspect_on_managed208_H'}or safe.get('private_exception_message_emitted')is not False:malformed+=1;continue
   cls=safe.get('exception_class')
   if cls is not None and(not isinstance(cls,str)or len(cls)>128 or not cls.isidentifier()):malformed+=1;continue
   if v['state']==REFUSED_STATE and cls is None:malformed+=1;continue
   frames=v.get('trace_locations',[])
   if not isinstance(frames,list)or len(frames)>64 or any(not isinstance(row,dict)or set(row)!={'file','function','line'}or not isinstance(row['file'],str)or len(row['file'])>2048 or not isinstance(row['function'],str)or len(row['function'])>128 or type(row['line'])is not int or row['line']<1 for row in frames):malformed+=1;continue
   safe['trace_locations']=frames;safe['stream']=stream
   for k in ('request_sha256','prospective209_input_sha256','inspected_installed208_input_sha256'):
    value=v.get(k)
    if isinstance(value,str)and len(value)==64 and all(c in '0123456789abcdef'for c in value):safe[k]=value
   records.append(safe)
 return dict(captured_exit_code=returncode,structured_records=records,nonrecord_lines=other,malformed_records=malformed,exitcode_captured_before_parsing=True,raw_nonrecord_text_emitted=False,execution_grant=False)

def main():
 if not(__debug__ and sys.flags.isolated and sys.dont_write_bytecode and sys.argv[1:]==['--inspect-root-built-request-before-admission']):raise ValueError('explicit_isolated_Root_readonly_inspect_required')
 for which,cap in [(resource.RLIMIT_CPU,120),(resource.RLIMIT_AS,2*1024**3)]:
  hard=resource.getrlimit(which)[1];limit=cap if hard==resource.RLIM_INFINITY else min(cap,hard);resource.setrlimit(which,(limit,limit))
 phase='source_ref_validation';denials=dict(filesystem=0,hard=0)
 try:
  # Audited Python regression guard, not a hostile/native sandbox. Filesystem
  # denial has normal OS semantics; no actual mutation is allowed or allowlisted.
  def audit(event,args):
   filesystem={'os.mkdir','os.rename','os.remove','os.rmdir','os.link','os.symlink','os.truncate','os.utime','os.chmod','os.chown','os.setxattr','os.removexattr'}
   hard={'subprocess.Popen','pty.spawn','os.system','os.fork','os.forkpty','os.posix_spawn','os.exec','os.spawn','os.startfile','os.startfile/2','os.chdir','os.kill','os.killpg','os.putenv','os.unsetenv'}
   write_open=event=='open'and isinstance(args[2],int)and args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
   if event in filesystem or write_open:
    denials['filesystem']+=1;exc=PermissionError(errno.EACCES,'readonly_consumer_filesystem_mutation_denied');exc.frw_fixed_code='READONLY_CONSUMER_FILESYSTEM_MUTATION_DENIED';raise exc
   if event.startswith('socket.')or event in hard:
    denials['hard']+=1;exc=RuntimeError('readonly_consumer_hard_effect_denied');exc.frw_fixed_code='READONLY_CONSUMER_HARD_EFFECT_DENIED';raise exc
  sys.addaudithook(audit)
  sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
  pins=json.loads((B/'SOURCE-PINS.json').read_bytes());path=B/'publication/friday_v3_layer_publication.py'
  if pins['source_refs'][str(path)]!=sha(path):raise ValueError('frozen_publisher_required')
  request_raw=(B/'ROOT-FRESH-REQUEST.json').read_bytes();request_digest=hashlib.sha256(request_raw).hexdigest();q=json.loads(request_raw);current=q['current_input']
  if sha(current['path'])!=current['sha256']:raise ValueError('current_input_drift')
  previous_ref=q['previous_input']
  if sha(previous_ref['path'])!=previous_ref['sha256']:raise ValueError('previous_input_drift')
  previous=json.loads(Path(previous_ref['path']).read_bytes());predecessor_ref=q['current_source_successor']['previous_native_update']
  if sha(predecessor_ref['path'])!=predecessor_ref['sha256']:raise ValueError('canonical208_request_drift')
  installed_request=json.loads(Path(predecessor_ref['path']).read_bytes())
  if installed_request['current_input']!=previous_ref:raise ValueError('canonical208_input_join_required')
  managed_home='/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032'
  previous_project=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112/project497')
  if any(value.get('home')!=managed_home for value in (q,previous,installed_request)):raise ValueError('managed208_home_join_required')
  if q['installed_layers']!=208 or q['layer_names']!=['f07-bounded-docx-structure-after-source208']or q['current_source_successor']['schema']!='friday.current-source-native-successor.v11':raise ValueError('exact209_request_required')
  phase='unmodified_source497_default_spec_inspect_on_managed208_H'
  sp=importlib.util.spec_from_file_location('Root209_whole_readonly_consumer',path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
  m.current_source_consumer_checked(previous,installed_request,previous_project,committed=True,inspect=True)
  if sha(B/'ROOT-FRESH-REQUEST.json')!=request_digest:raise ValueError('built_request_changed_across_inspect')
  print(json.dumps(dict(schema=RECORD_SCHEMA,state=PASS_STATE,phase=phase,exception_class=None,fixed_code='SOURCE_PINNED_CURRENT208_PREFLIGHT_COMPLETED',trace_locations=[],private_exception_message_emitted=False,request_sha256=request_digest,prospective209_input_sha256=current['sha256'],inspected_installed208_input_sha256=previous_ref['sha256'],consumer_origin='GENUINE_RETAINED_PRIVATE497_SOURCE',managed_home=managed_home,guard_denials=denials,source_only_not_install_or_runtime=True)))
 except BaseException as exc:
  fixed=getattr(exc,'frw_fixed_code',None);fixed=fixed if isinstance(fixed,str)and fixed in FIXED_CODES else'SOURCE_PINNED_CURRENT208_PREFLIGHT_FAILED'
  print(json.dumps(dict(schema=RECORD_SCHEMA,state=REFUSED_STATE,phase=phase,exception_class=type(exc).__name__,fixed_code=fixed,trace_locations=trace_locations(exc.__traceback__),private_exception_message_emitted=False,guard_denials=denials)),file=sys.stderr)
  raise SystemExit(2)from None
if __name__=='__main__':main()
