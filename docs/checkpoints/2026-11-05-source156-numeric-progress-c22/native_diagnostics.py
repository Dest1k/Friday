"""Source-only NativeDiagnostics excerpt, with no caller or entry point.

The selected class text is unchanged. Only required standard-library imports
are retained. Caller package values, including REGRESSION_MODULE, are omitted.
This excerpt is for source inspection; it is not a standalone diagnostic tool.
"""
from pathlib import Path
import json, os, re, signal, sys, time, types

class NativeDiagnostics:
 """Bounded CPU samples and authenticated numeric helper progress, never authority.

 No Python-call observer runs. Category call counts are not collected. A CPU
 pulse captures stacks and available cumulative helper stats at intervals;
 a blocked C/IO call can defer delivery. Samples never replace a policy check.
 """
 SAMPLE_SECONDS=10.0
 CPU_PULSE_SECONDS=1.0
 NORMAL_ROWS=120
 MAX_ROWS=128
 MAX_ROW_BYTES=65536
 MAX_FILE_BYTES=MAX_ROWS*MAX_ROW_BYTES
 MAX_CODES=64
 MAX_METADATA=1024
 MAX_STAGES=24
 STACK_FRAMES=12
 COUNTER_MAX=(1<<63)-1
 MAX_PROGRESS_KEYS=64
 MAX_CLASS_KEYS=64
 MAX_LOCALS_KEYS=128
 CATEGORIES=('read','walk','helper','parent_validation','decode','module_load')
 PROGRESS_INTS=('closed_validations','closed_hits','protected_reads','checks')
 PROGRESS_FLOATS=('check_wall_seconds','validation_wall_seconds')
 PROGRESS_OPTIONAL_INTS=('inventory_calls','helper_module_loads','fresh_grant_calls')
 PROGRESS_OPTIONAL_FLOATS=('inventory_wall_seconds','inventory_cpu_seconds','fresh_grant_wall_seconds','fresh_grant_cpu_seconds')
 def __init__(self,path,deadline,package,caller):
  import hashlib,functools,_functools
  self.hashlib=hashlib;self.deadline=deadline
  metadata_source=self._metadata_record
  self.metadata_cache=functools.lru_cache(maxsize=self.MAX_METADATA)(metadata_source)
  self.metadata_cache_owner=(self.metadata_cache,metadata_source,
   metadata_source.__func__.__code__,_functools._lru_cache_wrapper,
   self._fingerprint.__func__,self._fingerprint.__func__.__code__)
  self.path=path;self.package=package;self.caller=caller
  self.fd=None;self.active=False;self.busy=False;self.rows=0;self.bytes=0
  self.started=(time.monotonic(),time.process_time());self.last_sample=self.started[0]
  self.total={name:None for name in self.CATEGORIES};self.stages={};self.codes={}
  self.overflow_calls=0;self.stage_overflow=0;self.calls=None;self.pulses=0
  self.identity_chain=hashlib.sha256();self.identity_events=0;self.last_error_class=None;self.cleanup_error_class=None
  self.handler=self._pulse;self.previous_signal=None;self.signal_claimed=False;self.timer_started=False
  self.progress_path=None;self.progress_codes={};self.progress_check=None
  self.progress_authentication='NOT_AVAILABLE';self.progress_error_class=None
  self.progress_sample_status='NOT_AVAILABLE'
  self.frame_locals_type=type(sys._getframe().f_locals)
  self._prepare_progress(package)
 def _inc(self,value):return min(self.COUNTER_MAX,value+1)
 def _fingerprint(self,code):
  # Canonical static code fields, independent of marshal reference flags or
  # interpreter quickening. Runtime locals/globals/closures are never accessed.
  digest=self.hashlib.sha256()
  def field(sink,tag,raw):
   sink.update(tag);sink.update(len(raw).to_bytes(8,'big'));sink.update(raw)
  def value(sink,item):
   kind=type(item)
   if item is None:field(sink,b'N',b'')
   elif item is Ellipsis:field(sink,b'E',b'')
   elif kind is bool:field(sink,b'B',b'1'if item else b'0')
   elif kind is int:field(sink,b'I',str(item).encode('ascii'))
   elif kind is float:field(sink,b'F',item.hex().encode('ascii'))
   elif kind is complex:field(sink,b'X',(item.real.hex()+','+item.imag.hex()).encode('ascii'))
   elif kind is str:field(sink,b'S',item.encode('utf-8','surrogatepass'))
   elif kind is bytes:field(sink,b'Y',item)
   elif kind is tuple:
    field(sink,b'T',str(len(item)).encode('ascii'))
    for child in item:value(sink,child)
   elif kind is frozenset:
    field(sink,b'R',str(len(item)).encode('ascii'))
    encoded=[]
    for child in item:
     child_sink=self.hashlib.sha256();value(child_sink,child);encoded.append(child_sink.digest())
    for child_hash in sorted(encoded):field(sink,b'V',child_hash)
   elif kind is slice:
    field(sink,b'L',b'')
    for child in (item.start,item.stop,item.step):value(sink,child)
   elif kind is types.CodeType:
    field(sink,b'C',b'CODE_STATIC_FIELDS_V2')
    for name in ('co_filename','co_name','co_qualname','co_firstlineno','co_argcount',
      'co_posonlyargcount','co_kwonlyargcount','co_nlocals','co_stacksize','co_flags',
      'co_code','co_linetable','co_exceptiontable','co_consts','co_names','co_varnames','co_freevars','co_cellvars'):
     field(sink,b'K',name.encode('ascii'));value(sink,getattr(item,name))
   else:raise ValueError('static_code_constant_type_required')
  value(digest,code);return digest.hexdigest()

 @classmethod
 def preflight(cls,caller,package,read):
  # Compile the real pinned caller and every eligible declared source, including
  # nested code constants. No producer/caller body, history or native API runs.
  import hashlib
  probe=cls.__new__(cls);probe.hashlib=hashlib;rows=[]
  sources=[('caller',caller),('canonical_consumer',package['canonical_consumer'])]
  sources.extend((role,pin)for role,pin in sorted(package['files'].items())if role.endswith('.py'))
  for role,pin in sources:
   raw=read(pin);code=compile(raw,pin['path'],'exec',dont_inherit=True)
   rows.append(dict(role=role,source=pin,code_sha256=probe._fingerprint(code)))
  return dict(schema='frw.Root.native-diagnostic-static-preflight.v1',
   code_fingerprint='CODE_STATIC_FIELDS_V2',interpreter=list(sys.version_info[:3]),
   caller=caller,sources=rows,compiled_sources=len(rows),
   producer_or_history_or_native_body_executed=False,acceptance='NOT_ESTABLISHED')

 def _metadata_record(self,key,code):
  # The retained strong code object makes its issued id unambiguous. All
  # fields are immutable; no globals, defaults, closures or verdicts are cached.
  if key!=id(code) or type(code)is not types.CodeType:raise ValueError('native_diagnostic_code_identity_required')
  return (('file',re.sub('[^A-Za-z0-9_.<>-]','_',Path(code.co_filename).name[:80])),
   ('function',re.sub('[^A-Za-z0-9_.<>-]','_',code.co_qualname[:96])),
   ('first_line',code.co_firstlineno),('code_sha256',self._fingerprint(code)))

 def _metadata(self,code):
  cache,source,source_code,cache_type,fingerprint,fingerprint_code=self.metadata_cache_owner
  if (self.metadata_cache is not cache or type(cache)is not cache_type
      or cache.__wrapped__ is not source or source.__self__ is not self
      or self._metadata_record.__func__ is not source.__func__
      or source.__func__.__code__ is not source_code
      or source.__func__.__defaults__ is not None or source.__func__.__kwdefaults__ is not None
      or source.__func__.__closure__ is not None
      or self._fingerprint.__func__ is not fingerprint or fingerprint.__code__ is not fingerprint_code):
   raise ValueError('native_diagnostic_metadata_cache_binding_changed')
  # SIGPROF may re-enter an in-progress callback. Opaque LRU publication is
  # native; a miss computes immutable metadata and hits return a new dict.
  return dict(cache(id(code),code))

 def _prepare_progress(self,package):
  # Static pinned source only. No module/function body or retained verdict runs.
  # Failure disables numeric frame extraction; ordinary stack sampling remains.
  def source_pin(pin):
   # Screen key types before dictionary lookups/equality; a colliding foreign
   # key must not execute Python callbacks even during telemetry preparation.
   if(type(pin)is not dict or len(pin)!=2 or any(type(key)is not str for key in pin)
       or set(pin)!={'path','sha256'} or type(pin['path'])is not str
       or type(pin['sha256'])is not str or re.fullmatch('[a-f0-9]{64}',pin['sha256'])is None):
    raise ValueError('diagnostic_exact_source_pin_required')
   return pin['path'],pin['sha256']
  def exact(pin,limit):
   import stat
   source_pin(pin)
   fd=None
   try:
    # Publish descriptor ownership before delivering a pending original stop.
    # Nonblocking open keeps this tiny acquisition section finite for FIFOs.
    previous=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM,signal.SIGTERM,signal.SIGINT})
    try:fd=os.open(pin['path'],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)
    before=os.fstat(fd)
    if not stat.S_ISREG(before.st_mode)or not 0<before.st_size<=limit:raise ValueError('bounded_diagnostic_source_required')
    raw=b''
    while len(raw)<=limit:
     part=os.read(fd,min(65536,limit+1-len(raw)))
     if not part:break
     raw+=part
    after=os.fstat(fd)
    identity=lambda value:tuple(getattr(value,name)for name in('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
    if(identity(before)!=identity(after) or len(raw)!=before.st_size or self.hashlib.sha256(raw).hexdigest()!=pin['sha256']):
     raise ValueError('diagnostic_source_pin_changed')
    return raw
   finally:
    if fd is not None:os.close(fd)
  try:
   doc=json.loads(exact(package,1048576));pin=doc['files']['regression_attempt.py']
   if source_pin(pin)!=source_pin(REGRESSION_MODULE):
    raise ValueError('diagnostic_runtime_package_helper_binding_changed')
   raw=exact(pin,1048576);module=compile(raw,pin['path'],'exec',dont_inherit=True)
   classes=[code for code in module.co_consts if type(code)is types.CodeType and code.co_name=='InvocationSnapshot']
   if len(classes)!=1:raise ValueError('diagnostic_known_helper_class_required')
   codes=[code for code in classes[0].co_consts if type(code)is types.CodeType]
   if not 1<=len(codes)<=32:raise ValueError('bounded_diagnostic_helper_methods_required')
   expected={(code.co_name,code.co_firstlineno):self._fingerprint(code)for code in codes}
   checks=[value for (name,line),value in expected.items()if name=='check']
   if len(checks)!=1:raise ValueError('diagnostic_known_helper_check_required')
   self.progress_path=pin['path'];self.progress_codes=expected;self.progress_check=checks[0]
   self.progress_authentication='PINNED_HELPER_CODE_CLASS_SELF_BINDING_DIAGNOSTIC_ONLY'
  except Exception as error:self.progress_error_class=type(error).__name__
 def _progress(self,frame,metadata):
  # Read only fixed keys from the exact original helper frame/class and exact
  # builtin containers. No raw locals, paths, user strings or object repr escape.
  if type(frame)is not types.FrameType:return None
  code=frame.f_code
  expected=self.progress_codes.get((code.co_name,code.co_firstlineno))
  if code.co_filename!=self.progress_path or expected is None:return None
  self.progress_sample_status='HELPER_CODE_REJECTED'
  if metadata['code_sha256']!=expected:return None
  self.progress_sample_status='HELPER_RUNTIME_BINDING_REJECTED'
  namespace=frame.f_globals
  if type(namespace)is not dict or len(namespace)>512 or any(type(key)is not str for key in namespace):return None
  filename=namespace.get('__file__')
  if type(filename)is not str or filename!=self.progress_path:return None
  cls=namespace.get('InvocationSnapshot')
  if type(cls)is not type:return None
  members=type.__getattribute__(cls,'__dict__')
  if(len(members)>self.MAX_CLASS_KEYS or any(type(key)is not str or len(key)>128 for key in members)):return None
  check=members.get('check')
  if(type(check)is not types.FunctionType or check.__globals__ is not namespace
      or self._metadata(check.__code__)['code_sha256']!=self.progress_check):return None
  method=members.get(code.co_name)
  if(type(method)is not types.FunctionType or method.__globals__ is not namespace
      or method.__code__ is not code):return None
  local=frame.f_locals
  if((type(local)is not dict and type(local)is not self.frame_locals_type) or len(local)>self.MAX_LOCALS_KEYS
      or any(type(key)is not str or len(key)>128 for key in local)):return None
  owner=local.get('self')
  if type(owner)is not cls:return None
  descriptor=members.get('__dict__')
  if type(descriptor)is not types.GetSetDescriptorType or descriptor.__objclass__ is not cls:return None
  state=descriptor.__get__(owner,cls)
  if type(state)is not dict or len(state)>64 or any(type(key)is not str for key in state):return None
  if state.get('_class')is not cls:return None
  stats=state.get('stats')
  self.progress_sample_status='HELPER_STATS_REJECTED'
  required=self.PROGRESS_INTS+self.PROGRESS_FLOATS
  # Real invocation wrappers add helper loads, fresh grants and nested scope
  # timings. Ignore undeclared fields; emit only fixed, checked numeric fields.
  if(type(stats)is not dict or not len(required)<=len(stats)<=self.MAX_PROGRESS_KEYS
      or any(type(key)is not str or len(key)>64 for key in stats)
      or not set(required)<=set(stats)):return None
  values={}
  for name in self.PROGRESS_INTS+self.PROGRESS_OPTIONAL_INTS:
   if name not in stats:continue
   value=stats[name]
   if type(value)is not int or not 0<=value<=self.COUNTER_MAX:return None
   values[name]=value
  for name in self.PROGRESS_FLOATS+self.PROGRESS_OPTIONAL_FLOATS:
   if name not in stats:continue
   value=stats[name]
   if type(value)is not float or not 0.0<=value<=1e9:return None
   values[name]=value
  for field,name,kind in(('_files','remembered_files',dict),('_namespaces','remembered_namespaces',dict),
    ('_closed','sealed_records',dict),('_functions','function_bindings',dict),('_methods','method_bindings',dict),
    ('_libraries','library_bindings',tuple),('_constant_names','source_constants',tuple)):
   value=state.get(field)
   if type(value)is not kind:return None
   values[name]=len(value)
  self.progress_sample_status='SAMPLED'
  return dict(kind='INVOCATION_SNAPSHOT_CUMULATIVE_STATS_SAMPLE',values=values,
   semantics='SAMPLED_CURRENT_BUILTIN_COUNTERS_NOT_CALL_COUNTS_OR_VERDICTS',check_in_progress=code.co_name=='check')
 def _pulse(self,signum,frame):
  self.pulses=self._inc(self.pulses)
  if self.active and not self.busy and time.monotonic()-self.last_sample>=self.SAMPLE_SECONDS:
   self.safe_snapshot('INTERMEDIATE',frame)
 def snapshot(self,event,frame=None,error_class=None):
  if self.fd is None or self.busy:return
  if event not in('ENTER','INTERMEDIATE','RETURN','DEADLINE','CANCEL','ERROR'):raise ValueError('fixed_native_diagnostic_event_required')
  if self.rows>=self.MAX_ROWS or(self.rows>=self.NORMAL_ROWS and event in('ENTER','INTERMEDIATE')):return
  if error_class is not None and(type(error_class)is not str or re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]{0,95}',error_class)is None):raise ValueError('safe_native_error_class_required')
  self.busy=True
  try:
   now=time.monotonic();cpu=time.process_time();stack=[];progress=None
   self.progress_sample_status='NOT_OBSERVED_IN_BOUNDED_STACK'if self.progress_codes else'NOT_AVAILABLE'
   if frame is None:frame=sys._getframe(1)
   for _ in range(self.STACK_FRAMES):
    if frame is None:break
    code=frame.f_code;metadata=self._metadata(code)
    if progress is None:progress=self._progress(frame,metadata)
    stack.append(dict(metadata,line=frame.f_lineno))
    key=id(code);record=self.codes.get(key)
    if record is not None and record[0]is code:record[2]=self._inc(record[2])
    else:
     if len(self.codes)>=self.MAX_CODES:
      del self.codes[next(iter(self.codes))];self.overflow_calls=self._inc(self.overflow_calls)
     self.codes[key]=[code,metadata,1]
     self.identity_chain.update(bytes.fromhex(metadata['code_sha256']));self.identity_events=self._inc(self.identity_events)
    frame=frame.f_back
   phase=self.deadline.phase;stage=self.stages.get(phase)
   if stage is None and len(self.stages)<self.MAX_STAGES:
    stage=dict(samples=0,last_native_wall_elapsed_seconds=0.0,last_native_cpu_elapsed_seconds=0.0)
    self.stages[phase]=stage
   if stage is None:self.stage_overflow=self._inc(self.stage_overflow)
   else:
    stage['samples']=self._inc(stage['samples'])
    stage['last_native_wall_elapsed_seconds']=now-self.started[0]
    stage['last_native_cpu_elapsed_seconds']=cpu-self.started[1]
   row=dict(schema='frw.Root.native-continuation-intermediate.v1',ordinal=self.rows,event=event,
    phase=phase,monotonic=now,cpu_seconds=cpu,
    native_wall_elapsed_seconds=now-self.started[0],native_cpu_elapsed_seconds=cpu-self.started[1],
    original_origin_monotonic=self.deadline.origin,original_deadline_monotonic=self.deadline.hard_deadline,
    current_cutoff_monotonic=self.deadline.cutoff,error_class=error_class,
    code_fingerprint='CODE_STATIC_FIELDS_V2',package=self.package,caller=self.caller,counters=self.total.copy(),by_phase=self.stages,
    observed_python_calls=None,observed_selected_python_calls=None,
    counter_semantics='NOT_COLLECTED_NO_PYTHON_CALL_OBSERVER',cpu_pulses=self.pulses,
    progress=progress,progress_status='SAMPLED'if progress is not None else self.progress_sample_status,
    progress_authentication=self.progress_authentication,progress_authentication_error_class=self.progress_error_class,
    code_inventory=[dict(metadata,stack_sample_occurrences=count)for code,metadata,count in self.codes.values()],
    code_inventory_evictions=self.overflow_calls,code_identity_events=self.identity_events,
    code_identity_sequence_sha256=self.identity_chain.hexdigest(),stage_inventory_overflow_samples=self.stage_overflow,
    stack=stack,stack_truncated=frame is not None,
    sampling=dict(wall_interval_seconds=self.SAMPLE_SECONDS,cpu_pulse_seconds=self.CPU_PULSE_SECONDS,
     blocked_C_or_IO_wall_sampling=False,arbitrary_C_signal_delivery_may_defer=True,
     code_inventory_policy='BOUNDED_STACK_SAMPLES_ONLY',python_call_observer='NONE',
     selected_categories=self.CATEGORIES,category_call_counts='NOT_COLLECTED',
     progress_policy='FIXED_EXACT_BUILTIN_NUMERIC_STATS_FROM_PINNED_HELPER_FRAME',
     normal_row_cap=self.NORMAL_ROWS,row_cap=self.MAX_ROWS,row_byte_cap=self.MAX_ROW_BYTES,
     file_byte_cap=self.MAX_FILE_BYTES,code_cap=self.MAX_CODES,stage_cap=self.MAX_STAGES,
     stack_frame_cap=self.STACK_FRAMES),acceptance='NOT_ESTABLISHED')
   raw=(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n').encode('ascii')
   if len(raw)>self.MAX_ROW_BYTES or self.bytes+len(raw)>self.MAX_FILE_BYTES:raise ValueError('bounded_native_diagnostic_record_required')
   view=memoryview(raw)
   while view:
    written=os.write(self.fd,view)
    if written<=0:raise OSError('native_diagnostic_write_failed')
    view=view[written:]
   os.fsync(self.fd);self.rows+=1;self.bytes+=len(raw);self.last_sample=now
  finally:self.busy=False;del frame
 def safe_snapshot(self,event,frame=None,error_class=None):
  # Telemetry failure must never replace the original stop/native exception.
  try:self.snapshot(event,frame,error_class)
  except Exception as diagnostic_error:self.last_error_class=type(diagnostic_error).__name__

 def summary(self):
  return dict(path=str(self.path),rows=self.rows,bytes=self.bytes,
   diagnostic_error_class=self.last_error_class,cleanup_error_class=self.cleanup_error_class,
   acceptance='NOT_ESTABLISHED')

 def start(self):
  import threading
  if(threading.current_thread()is not threading.main_thread()
      or self.active or self.deadline.native_diagnostics is not None
      or signal.getitimer(signal.ITIMER_PROF)!=(0.0,0.0)
      or signal.getsignal(signal.SIGPROF)is not signal.SIG_DFL
      or sys.getprofile()is not None or sys.gettrace()is not None):raise ValueError('exclusive_native_diagnostic_owner_required')
  self.deadline.check()
  try:
   self.fd=os.open(self.path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
   directory=os.open(self.path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
   try:os.fsync(directory)
   finally:os.close(directory)
   self.previous_signal=signal.getsignal(signal.SIGPROF)
   self.signal_claimed=True;signal.signal(signal.SIGPROF,self.handler)
   self.active=True;self.deadline.native_diagnostics=self
   signal.setitimer(signal.ITIMER_PROF,self.CPU_PULSE_SECONDS,self.CPU_PULSE_SECONDS);self.timer_started=True
   self.snapshot('ENTER')
  except BaseException:
   try:self.close()
   except Exception as cleanup_error:self.cleanup_error_class=type(cleanup_error).__name__
   raise
  return self
 def close(self):
  conflicts=[];self.active=False
  if self.deadline.native_diagnostics is self:self.deadline.native_diagnostics=None
  if self.signal_claimed:
   handler=signal.getsignal(signal.SIGPROF);timer=signal.getitimer(signal.ITIMER_PROF)
   if handler is self.handler and(timer[1]==self.CPU_PULSE_SECONDS or(not self.timer_started and timer==(0.0,0.0))):
    signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,self.previous_signal)
   else:conflicts.append('profiling_owner_changed')
   self.signal_claimed=False
  if self.fd is not None:os.close(self.fd);self.fd=None
  cache=self.metadata_cache_owner[0]
  if type(cache)is self.metadata_cache_owner[3]:cache.cache_clear()
  self.progress_codes.clear()
  if conflicts:
   self.cleanup_error_class='ValueError'
   raise ValueError('native_diagnostic_owner_changed')
