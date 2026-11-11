"""Root-only F06 operation parent; --check never admits or launches anything."""
import argparse,ctypes,datetime,fcntl,hashlib,json,os,re,resource,signal,stat,subprocess,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent;sys.path.insert(0,str(B))
import f06_contract as c
PROPS='Id,LoadState,ActiveState,SubState,MainPID,ControlPID,ControlGroup,InvocationID,Description,ExecStart,ExecMainStartTimestampMonotonic,ExecMainExitTimestampMonotonic,ExecMainCode,ExecMainStatus,CPUUsageNSec,Result,RemainAfterExit,CollectMode,RuntimeMaxUSec,KillMode,Job,Restart,NRestarts,ExecStop,ExecStopPost'
NOT_FOUND_PROPS={'Id','LoadState','MainPID','ControlPID','ControlGroup'}
EXEC_ARRAY_PROPS={'ExecStop','ExecStopPost'}
need=c.need
def unit_props(unit,allow_missing=False):
    p=subprocess.run(['/usr/bin/systemctl','--user','--all','show',unit,'--property='+PROPS],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=3,check=False)
    rows=dict(line.split('=',1) for line in p.stdout.splitlines() if '=' in line)
    need(p.returncode==0 or allow_missing and rows.get('LoadState')=='not-found','FRAME_MANAGER_SHOW_FAILED')
    if allow_missing and rows.get('LoadState')=='not-found':
        # An absent unit has no runtime/stop-path evidence. Admission requires
        # only these actual fields; no service property is invented here.
        need(NOT_FOUND_PROPS <= set(rows),'FRAME_MANAGER_PROPERTIES_MISSING')
        need(rows['Id']==unit,'FRAME_MANAGER_UNIT_CHANGED')
        return rows
    missing=set(PROPS.split(','))-set(rows)
    need(not missing-EXEC_ARRAY_PROPS,'FRAME_MANAGER_PROPERTIES_MISSING')
    if missing:
        # systemctl omits empty Exec* arrays even with --all. Fill a field only
        # after a typed, present, genuinely empty D-Bus property is observed.
        bus=Bus(unit=unit)
        try:
            evidence=[]
            for name in sorted(missing):
                evidence.append(bus.empty_exec_property(name));rows[name]=''
            rows['_frw_typed_empty_exec_arrays']=evidence
        finally: bus.close()
    need(set(PROPS.split(',')) <= set(rows),'FRAME_MANAGER_PROPERTIES_MISSING')
    return rows

def no_job(props):
    need('Job' in props,'FRAME_MANAGER_PROPERTIES_MISSING')
    return props['Job'] in ('','0 /','0')

def cgroup_members(cgroup,unit):
    root=Path(cgroup)
    need(str(root).startswith('/sys/fs/cgroup/') and root.name==unit,'FRAME_CGROUP_SCOPE')
    members=[];entries=0;deadline=time.monotonic()+2
    def traversal_error(error): raise error
    if root.exists():
        need(not root.is_symlink() and root.is_dir(),'FRAME_CGROUP_DIRECTORY')
        for parent,dirs,files in os.walk(root,followlinks=False,onerror=traversal_error):
            entries+=1+len(dirs)+len(files)
            need(entries<=4096 and time.monotonic()<deadline,'FRAME_CGROUP_TRAVERSAL_BOUND')
            need(all(not (Path(parent)/name).is_symlink() for name in dirs),'FRAME_CGROUP_LINK')
            if 'cgroup.procs' in files:
                fd=os.open(Path(parent)/'cgroup.procs',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
                try: raw=os.read(fd,8193);need(len(raw)<=8192,'FRAME_CGROUP_PROCS_CAP')
                finally: os.close(fd)
                members.extend((str(Path(parent)/'cgroup.procs'),int(x)) for x in raw.split())
                need(len(members)<=128,'FRAME_CGROUP_MEMBER_CAP')
    return members

def owned_actors(unit):
    rows=[];count=0;scan_end=time.monotonic()+2
    for proc in Path('/proc').iterdir():
        count+=1;need(count<=65536 and time.monotonic()<scan_end,'FRAME_PROC_SCAN_BOUND')
        if not proc.name.isdecimal(): continue
        try:
            if proc.stat().st_uid!=os.getuid(): continue
            cg=(proc/'cgroup').read_text().splitlines()
            if any(row.split(':',2)[-1].endswith('/'+unit) or '/'+unit+'/' in row.split(':',2)[-1] for row in cg):
                rows.append(dict(pid=int(proc.name),stat=(proc/'stat').read_text()))
        except (FileNotFoundError,ProcessLookupError): pass
        except PermissionError: need(False,'FRAME_OWN_ACTOR_UNREADABLE')
    return rows

class Bus:
    """One ordinary sd-bus client retains this exact unit until real closure."""
    def __init__(self,unit):
        self.unit=unit
        self.lib=ctypes.CDLL('libsystemd.so.0'); self.bus=ctypes.c_void_p();self.held=False
        L=self.lib
        L.sd_bus_open_user.argtypes=[ctypes.POINTER(ctypes.c_void_p)];L.sd_bus_open_user.restype=ctypes.c_int
        L.sd_bus_set_method_call_timeout.argtypes=[ctypes.c_void_p,ctypes.c_uint64];L.sd_bus_set_method_call_timeout.restype=ctypes.c_int
        L.sd_bus_call_method.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p),ctypes.c_char_p];L.sd_bus_call_method.restype=ctypes.c_int
        L.sd_bus_message_unref.argtypes=[ctypes.c_void_p];L.sd_bus_message_unref.restype=ctypes.c_void_p
        L.sd_bus_flush_close_unref.argtypes=[ctypes.c_void_p];L.sd_bus_flush_close_unref.restype=ctypes.c_void_p
        L.sd_bus_get_property.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p),ctypes.c_char_p];L.sd_bus_get_property.restype=ctypes.c_int
        L.sd_bus_message_enter_container.argtypes=[ctypes.c_void_p,ctypes.c_char,ctypes.c_char_p];L.sd_bus_message_enter_container.restype=ctypes.c_int
        L.sd_bus_message_at_end.argtypes=[ctypes.c_void_p,ctypes.c_int];L.sd_bus_message_at_end.restype=ctypes.c_int
        L.sd_bus_message_exit_container.argtypes=[ctypes.c_void_p];L.sd_bus_message_exit_container.restype=ctypes.c_int
        try:
            need(L.sd_bus_open_user(ctypes.byref(self.bus))>=0,'FRAME_BUS_OPEN_FAILED')
            need(L.sd_bus_set_method_call_timeout(self.bus,2000000)>=0,'FRAME_BUS_TIMEOUT_FAILED')
        except BaseException:
            self.close();raise
    def call(self,method,signature=b'',*args,interface=b'org.freedesktop.systemd1.Manager'):
        reply=ctypes.c_void_p()
        rc=self.lib.sd_bus_call_method(self.bus,b'org.freedesktop.systemd1',b'/org/freedesktop/systemd1',interface,method.encode(),None,ctypes.byref(reply),signature,*[ctypes.c_char_p(v.encode()) for v in args])
        if reply: self.lib.sd_bus_message_unref(reply)
        need(rc>=0,'FRAME_BUS_METHOD_FAILED_'+method.upper())
    def ref(self): self.call('RefUnit',b's',self.unit);self.held=True
    def ping(self): self.call('Ping',interface=b'org.freedesktop.DBus.Peer')
    def empty_exec_property(self,name):
        need(name in EXEC_ARRAY_PROPS,'FRAME_READONLY_PROPERTY_SCOPE')
        need(re.fullmatch('[A-Za-z0-9_.-]+\\.service',self.unit),'FRAME_READONLY_UNIT_PATH')
        escaped=''.join(ch if ch.isascii() and ch.isalnum() else '_'+format(ord(ch),'02x') for ch in self.unit)
        reply=ctypes.c_void_p();L=self.lib
        try:
            rc=L.sd_bus_get_property(self.bus,b'org.freedesktop.systemd1',('/org/freedesktop/systemd1/unit/'+escaped).encode(),b'org.freedesktop.systemd1.Service',name.encode(),None,ctypes.byref(reply),b'a(sasbttttuii)')
            need(rc>=0 and bool(reply),'FRAME_EXEC_PROPERTY_READ_FAILED')
            need(L.sd_bus_message_enter_container(reply,b'a',b'(sasbttttuii)')>0,'FRAME_EXEC_PROPERTY_TYPE')
            need(L.sd_bus_message_at_end(reply,0)==1,'FRAME_EXEC_PROPERTY_NOT_EMPTY')
            # sd_bus_get_property leaves the reply inside its typed variant.
            need(L.sd_bus_message_exit_container(reply)>0 and L.sd_bus_message_exit_container(reply)>0 and L.sd_bus_message_at_end(reply,1)==1,'FRAME_EXEC_PROPERTY_MESSAGE')
            return dict(unit=self.unit,property=name,signature='a(sasbttttuii)',array_length=0,read_method='sd_bus_get_property')
        finally:
            if reply:L.sd_bus_message_unref(reply)
    def stop_owned(self):
        need(self.held,'FRAME_REFERENCE_REQUIRED')
        self.call('StopUnit',b'ss',self.unit,'fail')
    def release(self):
        need(self.held,'FRAME_REFERENCE_REQUIRED')
        self.call('UnrefUnit',b's',self.unit);self.held=False
    def close(self):
        if self.bus: self.lib.sd_bus_flush_close_unref(self.bus);self.bus=None

def run_argv(admission,sha):
 return ['/usr/bin/python3','-I','-B','-S',str(B/'run_once.py'),'--admission',str(admission),'--admission-sha256',sha]

def command(a,sha):
 unit=c.unit_name(a['operation_key']);lim=c.limits(a['mode']);cpustr=' '.join(map(str,a['actual_two_cpu_ids']))
 return ['/usr/bin/systemd-run','--user','--unit='+unit,'--slice=app.slice','--property=Type=exec','--property=Restart=no','--property=RemainAfterExit=yes','--property=CollectMode=inactive','--property=Description=FRW F06 once '+a['nonce'],'--property=RuntimeMaxSec='+str(lim['whole_wall_seconds']),'--property=TimeoutStopSec=5','--property=KillMode=control-group','--property=MemoryMax='+str(lim['memory_bytes']),'--property=MemorySwapMax=0','--property=CPUQuota=200%','--property=AllowedCPUs='+cpustr,'--property=CPUAffinity='+cpustr,'--property=TasksMax=128','--property=UMask=0077','--property=CPUAccounting=yes','--property=MemoryAccounting=yes','--property=TasksAccounting=yes']+run_argv(B/(a['operation_key']+'.ADMISSION.json'),sha)

def execstart_identity(value,expected):
 # systemctl appends mutable execution observations to this single command.
 # Full-match the one known grammar; never accept a matching substring in a
 # second command, extra argument, duplicate field, or changed command option.
 need(all(re.fullmatch(r'[A-Za-z0-9_./-]+',arg) for arg in expected),'UNIT_EXECSTART_EXPECTED_ARGV')
 suffix=r'(?:start_time=\[[^\]\r\n;{}]*\] ; stop_time=\[[^\]\r\n;{}]*\] ; pid=[0-9]+ ; code=[A-Za-z0-9_()-]+ ; status=[A-Za-z0-9_+./()-]+ )?'
 match=re.fullmatch(r'\{ path=([^ ;{}\r\n]+) ; argv\[\]=([^;{}\r\n]+) ; ignore_errors=(yes|no) ; '+suffix+r'\}',value)
 need(match is not None,'UNIT_EXACT_EXECSTART')
 identity=(match[1],match[2],match[3])
 need(identity==('/usr/bin/python3',' '.join(expected),'no'),'UNIT_EXACT_EXECSTART')
 return identity

def scope(props,a,sha,bound=None):
 unit=c.unit_name(a['operation_key']);lim=c.limits(a['mode'])
 need(props['Id']==unit and props['LoadState']=='loaded' and props['Description']=='FRW F06 once '+a['nonce'],'UNIT_NONCE_IDENTITY')
 need(re.fullmatch('[0-9a-f]{32}',props['InvocationID']) is not None and int(props['ExecMainStartTimestampMonotonic'])>0,'UNIT_INVOCATION_ORIGIN')
 need(props['RemainAfterExit']=='yes' and props['CollectMode']=='inactive' and props['KillMode']=='control-group' and props['Restart']=='no' and props['NRestarts']=='0' and not props['ExecStop'] and not props['ExecStopPost'],'UNIT_FINITE_RETENTION')
 need(props['RuntimeMaxUSec'] in (str(lim['whole_wall_seconds'])+'s',str(lim['whole_wall_seconds']*1000000)+'us','5min' if lim['whole_wall_seconds']==300 else '30s'),'UNIT_ORIGINAL_WALL')
 expected=run_argv(B/(a['operation_key']+'.ADMISSION.json'),sha)
 identity=execstart_identity(props['ExecStart'],expected)
 if bound:
  need(all(props[k]==bound[k] for k in ('Id','InvocationID','Description','ExecMainStartTimestampMonotonic')) and identity==execstart_identity(bound['ExecStart'],expected),'UNIT_BIRTH_SCOPE_CHANGED')
  need(props['ControlGroup'] in ('',bound['ControlGroup'],bound.get('_cgroup_rel')),'UNIT_CGROUP_CHANGED')
 return props

def slice_context():
 p=subprocess.run(['/usr/bin/systemctl','--user','show','app.slice','--property=Id,ActiveState,ControlGroup'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=3,check=True)
 props=dict(x.split('=',1) for x in p.stdout.splitlines())
 need(props.get('Id')=='app.slice' and props.get('ActiveState')=='active','EXISTING_ACTIVE_APP_SLICE')
 rel=props.get('ControlGroup','');need(rel.startswith('/') and Path(rel).name=='app.slice','EXISTING_APP_SLICE_CGROUP')
 root=Path('/sys/fs/cgroup'+rel);need(root.is_dir() and not root.is_symlink(),'ACTUAL_APP_SLICE_KERNEL_DIRECTORY')
 return props

def bind_cgroup(bound,op,unit,expected):
 need(expected.startswith('/sys/fs/cgroup/') and Path(expected).name==unit and Path(expected).parent.name=='app.slice','EXPECTED_CGROUP_SCOPE')
 rel=expected[len('/sys/fs/cgroup'):]
 need(bound['ControlGroup'] in ('',rel),'ACTUAL_CGROUP_VS_EXPECTED_SLICE')
 if (op/'UNIT-INTENT.json').exists():
  raw,pin=c.private(op/'UNIT-INTENT.json',c.B);intent=json.loads(raw)
  need(intent['unit']==unit and abs(intent['original_unit_start_monotonic']-int(bound['ExecMainStartTimestampMonotonic'])/1e6)<.000002 and intent['cgroup']==expected,'EARLY_EXIT_UNIT_INTENT_JOIN')
 bound['_cgroup_rel']=rel
 return expected

def children_cpu():
 value=resource.getrusage(resource.RUSAGE_CHILDREN)
 return value.ru_utime+value.ru_stime

def actual_exit(props):
 return props['MainPID']=='0' and props['ControlPID']=='0' and props['ActiveState'] in ('active','inactive','failed') and int(props['ExecMainCode'])>0 and int(props['ExecMainExitTimestampMonotonic'])>=int(props['ExecMainStartTimestampMonotonic'])

def kernel_empty(cg,unit,bound):
 need(cg.startswith('/sys/fs/cgroup/') and Path(cg).name==unit,'KERNEL_CGROUP_SCOPE')
 members=cgroup_members(cg,unit);actors=owned_actors(unit)
 pid=int(bound['MainPID'])
 if pid>0 and Path('/proc',str(pid)).exists():
  try:
   row=Path('/proc',str(pid),'stat').read_text().rsplit(') ',1)[1].split()
   if row[19]==bound.get('_main_starttime'):return False
  except FileNotFoundError:pass
 return not members and not actors

def proof(row):return c.runtime_pin_check(row)

RETAINED_PREFLIGHT_ROOT=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-OFFICE-GENERATION-20261111')
RETAINED_PREFLIGHT_PINS='4242f4ea8bfe6110e53103b88696058a4a286cbf78a4d0591846672574b27a66'
RETAINED_PREFLIGHT_FILES={
 'source_pins':('SOURCE-PINS.json',RETAINED_PREFLIGHT_PINS),
 'admission':('preflight-g1.ADMISSION.json','1437c5b118f18f1be13ab92b51f17da7d2ddc8831301d10a56fdbd1ba61a8c37'),
 'root_result':('operations/preflight-g1/ROOT-RESULT.json','a7ceafc81b42a871cdfc79edb09d492f71923eb618534df3b7bfb6d8a8729bac'),
 'unit_result':('operations/preflight-g1/UNIT-RESULT.json','f8a925f172a1b22f83e0daef068d6d720caaef508911181143e6eed7a5cb7a8d'),
 'inside_result':('operations/preflight-g1/work/INSIDE-RESULT.json','05420c3e831ead14003fab6a5d11d1eb08cde53132642ac1b0e4389c2d282897'),
 'typed_proof':('operations/preflight-g1/work/UNO-PREFLIGHT.json','a86b1d9d28a690dce483fde632209455d411aa9d2aeb601902930257b544d260'),
 'parent_binding':('operations/preflight-g1/PARENT-BINDING.json','45107cd9e5f1f4b917e3b70c50460a0317f23770cf3b387aae1c5996f888705a'),
 'unit_closure':('operations/preflight-g1/ROOT-RECONCILIATION-UNIT-CLOSED.json','b7fc6bbb7d528803db49d7a9aa6779a85ffc04202ac2972826a23333f70ef8c8'),
 'parent_closure':('operations/preflight-g1/ROOT-RECONCILIATION-FINAL-CLOSURE.json','d0036f50863963a1148a1efa412395f02403008518d4d495ed4536e3b83f92a5')}


def pin_join(left,right):
 need(type(left)is dict and type(right)is dict and all(left.get(k)==right.get(k)for k in ('path','bytes','sha256')),'PROOF_REFERENCE_JOIN')

def fresh_time(value,code,max_age=120):
 at=datetime.datetime.fromisoformat(value)
 need(at.utcoffset()==datetime.timedelta(hours=3),'PROOF_MOSCOW_TIMEZONE')
 age=(datetime.datetime.now(datetime.timezone.utc)-at).total_seconds();need(0<=age<=max_age,code)

def retained_support(a,review):
 # History proves exact typed-bank support, never current admission, boot,
 # replay permission, original-window PASS, or application/password semantics.
 row=a['retained_support'];pin_join(row,review['retained_support'])
 mapping,_=proof(row)
 need(mapping.get('schema')=='friday.f06.root-retained-typed-support.v1' and mapping.get('state')=='ROOT_ACCEPTED_RETAINED_TYPED_SUPPORT_MAPPING','RETAINED_SUPPORT_MAPPING')
 need(mapping.get('assignment')==c.ASSIGNMENT and mapping.get('source_pins_sha256')==a['source_pins_sha256'] and mapping.get('prior_source_pins_sha256')==RETAINED_PREFLIGHT_PINS,'RETAINED_SUPPORT_SOURCE_BINDING')
 need(mapping.get('bank_manifest_sha256')==c.MANIFEST_SHA and mapping.get('bank_root')==str(c.BASE),'RETAINED_SUPPORT_BANK')
 need(mapping.get('historical_only')is True and mapping.get('preflight_reexecuted')is False and mapping.get('original_window_PASS')is False and mapping.get('current_boot_claim')is False and mapping.get('application_or_password_PASS')is False,'RETAINED_SUPPORT_HONEST_SCOPE')
 need(mapping.get('actual_new_actor_imports_required')is True and mapping.get('unknown_support_differences')==[],'RETAINED_SUPPORT_APPLICABILITY')
 evidence=mapping.get('evidence');need(type(evidence)is dict and set(evidence)==set(RETAINED_PREFLIGHT_FILES),'RETAINED_SUPPORT_EXACT_NINE')
 observed={}
 for name,(relative,sha)in RETAINED_PREFLIGHT_FILES.items():
  ref=evidence[name];need(ref.get('path')==str(RETAINED_PREFLIGHT_ROOT/relative) and ref.get('sha256')==sha,'RETAINED_SUPPORT_HISTORICAL_PIN')
  observed[name]=proof(ref)[0]
 typed=observed['typed_proof'];inside=observed['inside_result'];closure=observed['unit_closure'];final=observed['parent_closure']
 need(typed.get('state')=='ISOLATED_EMBEDDED_UNO_TYPES_IMPORT_PASS_NO_OFFICE' and typed.get('Office_starts')==typed.get('document_loads')==typed.get('secret_reads')==0,'RETAINED_TYPED_HISTORICAL_STATE')
 expected_typed=dict(types=['PropertyValue','XInteractionHandler','DocumentPasswordRequest','DocumentMSPasswordRequest'],macro_NEVER_EXECUTE=0,update_NO_UPDATE=0)
 need(all(typed.get(k)==v for k,v in expected_typed.items()) and mapping.get('historical_typed_support')==expected_typed,'RETAINED_TYPED_SUPPORT_VALUES')
 need(inside.get('state')=='ISOLATED_UNO_PREFLIGHT_NO_OFFICE_PASS' and inside.get('owned_children_closed')is True,'RETAINED_INSIDE_HISTORICAL_STATE')
 need(closure.get('state')=='ROOT_EXACT_EXISTING_PREFLIGHT_UNIT_CLOSED_AFTER_CHECKER_FALSE_REFUSAL' and closure.get('preflight_reexecuted')is False and closure.get('late_closure_readback_not_original_window_PASS')is True,'RETAINED_CLOSURE_HISTORICAL_STATE')
 need(final.get('state')=='EXACT_PREFLIGHT_PARENT_REAPED_AND_SHARED_SLOT_FREE' and final.get('parent_absent')is True and final.get('operation_reexecuted')is False,'RETAINED_PARENT_HISTORICAL_STATE')
 return mapping

def native_closure(a,manifest,review):
 row=a['native_actors_closed'];pin_join(row,review['native_actors_closed']);closed,_=proof(row)
 need(closed.get('schema')=='friday.f06.root-native-actors-closed.v1' and closed.get('state')=='ROOT_OBSERVED_ORIGINAL_NATIVE_ACTORS_CLOSED','NATIVE_CLOSURE_SCHEMA')
 need(closed.get('assignment')==c.ASSIGNMENT and closed.get('native_operation_id')==manifest['native_operation_id'] and closed.get('uid')==a['uid'] and closed.get('boot_id')==a['boot_id'],'NATIVE_CLOSURE_LINEAGE')
 fresh_time(closed['observed_at_moscow'],'NATIVE_CLOSURE_FRESH_TIME')
 need(closed.get('actual_native_actors')==[] and closed.get('actual_native_requests')==[] and closed.get('actual_closed')is True and closed.get('reexecuted')is False,'NATIVE_ACTORS_ACTUALLY_CLOSED')
 for name in ('native_binding','native_root_grant','native_once'):
  pin_join(closed['native_evidence'][name],a['native_evidence'][name])
 births=closed.get('original_actor_births');need(type(births)is list and len(births)<=128,'NATIVE_ORIGINAL_ACTOR_BIRTHS')
 for birth in births:
  need(type(birth)is dict and type(birth.get('pid'))is int and birth['pid']>0 and type(birth.get('starttime'))is str and birth['starttime'].isdecimal() and birth.get('uid')==a['uid'],'NATIVE_ACTOR_BIRTH')
  path=Path('/proc')/str(birth['pid'])
  try:
   if path.stat().st_uid==a['uid']:
    current=(path/'stat').read_text().rsplit(') ',1)[1].split()[19]
    need(current!=birth['starttime'],'NATIVE_ORIGINAL_ACTOR_STILL_PRESENT')
  except (FileNotFoundError,ProcessLookupError):pass
 return closed

def readonly_effect_basis(a,manifest,review):
 row=a['readonly_effect_basis'];pin_join(row,review['readonly_effect_basis']);basis,_=proof(row)
 need(basis.get('schema')=='friday.f06.root-readonly-retained-effect-basis.v1' and basis.get('state')=='ROOT_ACCEPTED_DISTINCT_READONLY_RETAINED_ORACLE_ONLY','READONLY_EFFECT_BASIS')
 need(basis.get('assignment')==c.ASSIGNMENT and basis.get('native_operation_id')==manifest['native_operation_id'] and basis.get('new_operation_key')==a['operation_key'] and basis.get('new_source_pins_sha256')==a['source_pins_sha256'],'READONLY_EFFECT_LINEAGE')
 pin_join(basis['output_manifest'],a['output_manifest']);pin_join(basis['native_actors_closed'],a['native_actors_closed'])
 need(basis.get('selected_fixture_ids')==a['selected_fixture_ids'] and basis.get('expected_stores')==0 and basis.get('expected_probes')==3*a['selected_count'] and basis.get('native_effects_repeated')is False and basis.get('original_native_statuses_preserved')is True and basis.get('original_clocks_or_consumed_effects_reset')is False and basis.get('whole_F06_accepted')is False,'READONLY_DISTINCT_EFFECT_ONLY')
 need(basis.get('resolved_affected_unknowns')is True and basis.get('remaining_affected_unknowns')==[],'READONLY_AFFECTED_UNKNOWN_UNRESOLVED')
 need(c.exact_json(basis.get('limits'),a['limits']) and basis.get('original_operation_start_monotonic')==a['original_operation_start_monotonic'],'READONLY_EFFECT_CLOCK_LIMITS')
 return basis

def codec_review_bindings(a,review,observer):
 for joined in (review,observer):
  need(c.exact_json(joined.get('codec_acceptance'),a['codec_acceptance']),'CODEC_REVIEW_FULL_PIN_JOIN')
 return c.codec_acceptance(a['codec_acceptance'])

def validate_admission(path,sha):
 raw,pin=c.private(path,B);need(pin['sha256']==sha,'ADMISSION_SHA');a=c.decode(raw)
 mode=a['mode'];key=a['operation_key'];c.operation(key,mode);lim=c.limits(mode)
 credential,credential_identity=c.credential_metadata(a['credential_source']);c.PRE_STAGE_CREDENTIAL_PATHS.add(credential['path'])
 need(path==B/(key+'.ADMISSION.json') and a.get('schema')=='friday.f06.root-retained-output-once-admission.v1' and a.get('state')=='ROOT_FRESH_ONCE_ADMITTED' and a.get('assignment')==c.ASSIGNMENT,'ADMISSION_STATE_PATH')
 need(type(a.get('uid'))is int and a['uid']==os.getuid() and a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip() and type(a.get('nonce'))is str and re.fullmatch('[0-9a-f]{32}',a['nonce'])is not None,'ADMISSION_UID_BOOT_NONCE')
 fresh_time(a['admitted_at_moscow'],'ADMISSION_FRESH_TIME')
 origin=a.get('original_operation_start_monotonic')
 need(type(origin)in(int,float) and 0<=time.monotonic()-origin<=120,'ADMISSION_ORIGINAL_CLOCK')
 c.DEADLINE=origin+lim['whole_wall_seconds'];c.within(lim['cleanup_reserve_seconds'])
 need(a.get('source_pins_sha256')==c.recipe_check()[0]['sha256'] and c.exact_json(a.get('limits'),lim),'ADMISSION_SOURCE_LIMITS')
 cpus=a['actual_two_cpu_ids'];need(type(cpus)is list and len(cpus)==2 and len(set(cpus))==2 and all(type(x)is int for x in cpus) and set(cpus)<=os.sched_getaffinity(0),'ACTUAL_CPU_AFFINITY')
 review,_=proof(a['source_review'])
 need(review.get('state')=='ROOT_ACCEPTED_F06_RETAINED_OUTPUT_SOURCE' and review.get('source_pins_sha256')==a['source_pins_sha256'] and review.get('findings_remaining')==[] and review.get('new_readonly_route_reviewed')is True,'SOURCE_REVIEW')
 pin_join(review['canonical_fix_acceptance'],a['canonical_fix_acceptance'])
 pin_join(review['negative_observer_review'],a['negative_observer_review'])
 observer,_=proof(a['negative_observer_review'])
 _,source_rows=c.recipe_check();driver=next(p for p in source_rows if Path(p['path']).name=='office_fixture_driver.py')
 need(observer.get('state')=='ROOT_ACCEPTED_EXACT_PASSWORD_NEGATIVE_OBSERVER_SOURCE' and observer.get('source_pins_sha256')==a['source_pins_sha256'] and observer.get('driver_sha256')==driver['sha256'] and observer.get('generic_exception_is_expected_password_refusal')is False and observer.get('typed_password_refusal_required')is True and observer.get('same_retained_bytes_no_regeneration')is True and observer.get('findings_remaining')==[],'PASSWORD_NEGATIVE_OBSERVER_REVIEW_REQUIRED')
 codec_review_bindings(a,review,observer)
 fresh,_=proof(a['fresh_boundary'])
 need(fresh.get('state')=='ROOT_FRESH_F06_KERNEL_CUSTODY' and fresh.get('boot_id')==a['boot_id'] and fresh.get('uid')==os.getuid() and fresh.get('slot_identity')==a['slot_identity'],'ROOT_FRESH_PROOF')
 fresh_time(fresh['observed_at_moscow'],'BOUNDARY_FRESH_TIME')
 need(fresh['bank']==c.bank_snapshot(),'FRESH_BANK_METADATA_CAS_CRITICAL4')
 need(fresh.get('affinity_cpu_ids')==sorted(os.sched_getaffinity(0)) and fresh.get('memory_available_kib',0)>=3*1024*1024 and fresh.get('CPU_pressure_raw') and fresh.get('IO_pressure_raw'),'ROOT_RESOURCE_OBSERVATIONS')
 mem=dict((x.split(':',1)[0],x.split(':',1)[1].strip())for x in Path('/proc/meminfo').read_text().splitlines());need(int(mem['MemAvailable'].split()[0])>=3*1024*1024,'CURRENT_MEMORY_AVAILABLE')
 need('identity'in a['output_manifest'],'OUTPUT_MANIFEST_IDENTITY_REQUIRED')
 manifest,_,_,credential=c.output_inputs(a)
 need(c.credential_metadata(credential)[1]==a['credential_source_identity'],'CREDENTIAL_ADMISSION_IDENTITY')
 retained_support(a,review);native_closure(a,manifest,review);readonly_effect_basis(a,manifest,review)
 c.retention_snapshot(a['task_retention_root']);c.within(lim['cleanup_reserve_seconds'])
 return a,pin

def acquire_slot(a):
 need(str(c.SLOT)==a['slot_path'],'SLOT_EXACT_PATH')
 need(type(a.get('slot_identity'))is list and len(a['slot_identity'])==len(c.IDENTITY_FIELDS) and all(type(v)is int for v in a['slot_identity']),'SLOT_IDENTITY_SHAPE')
 for parent in c.SLOT.parents:need(not parent.is_symlink(),'SLOT_PARENT_LINK')
 fd=os.open(c.SLOT,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  s=os.fstat(fd);need(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o600 and s.st_nlink==1 and s.st_size==0,'SLOT_CUSTODY')
  need(c.identity(s)==a['slot_identity']==c.identity(c.SLOT.lstat()),'FRESH_SLOT_IDENTITY')
  fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);need(c.identity(os.fstat(fd))==c.identity(c.SLOT.lstat()),'LOCKED_SLOT_CAS');return fd
 except BaseException:os.close(fd);raise


def execute(args):
 entry_cpu=time.process_time();entry_children_cpu=children_cpu()
 c.CPU_GUARD=lambda:need(time.process_time()-entry_cpu+children_cpu()-entry_children_cpu<c.LIMITS['aggregate_CPU_seconds'],'ROOT_AGGREGATE_CPU_BUDGET')
 need(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'ROOT_INTERPRETER_FLAGS')
 # This is a future Root-only entry; source checks never execute it.
 a,ap=validate_admission(args.admission,args.admission_sha256);mode=a['mode'];lim=c.limits(mode);key=a['operation_key'];op=c.operation(key,mode);unit=c.unit_name(key)
 c.safe_dir(B);need(not os.path.lexists(op),'OPERATION_NO_REPLAY')
 ops=B/'operations'
 if not ops.exists():ops.mkdir(mode=0o700)
 c.safe_dir(ops);lockfd=acquire_slot(a);bus=None;launch=None;bound=None;cg=None;closed=False;pending=[]
 report=dict(state='PRELAUNCH_REFUSAL',mode=mode,operation_key=key,unit=unit,boot_id=a['boot_id'],source_pins_sha256=a['source_pins_sha256'],admission=ap,started_at_moscow=c.utcmoscow(),actual_closure_observed=False,launch_attempts=0)
 old={}
 def defer(sig,_):pending.append(sig)
 for sig in (signal.SIGINT,signal.SIGTERM):old[sig]=signal.signal(sig,defer)
 launch_start=time.monotonic();parent_cpu=entry_cpu;parent_children_cpu=entry_children_cpu;expected_cgroup=None
 try:
  slice_observation=slice_context();expected_cgroup='/sys/fs/cgroup'+slice_observation['ControlGroup']+'/'+unit;report['actual_existing_app_slice']=slice_observation;report['expected_kernel_cgroup']=expected_cgroup
  initial=unit_props(unit,True);need(initial['LoadState']=='not-found' and initial['MainPID']=='0' and initial['ControlPID']=='0' and not initial['ControlGroup'],'UNIT_ALREADY_EXISTS')
  op.mkdir(mode=0o700);c.save(op/'ROOT-INTENT.json',report)
  c.save(op/'PARENT-BINDING.json',dict(root_pid=os.getpid(),root_starttime=Path('/proc/self/stat').read_text().rsplit(') ',1)[1].split()[19],root_uid=os.getuid(),boot_id=a['boot_id'],admission_sha256=args.admission_sha256,slot_fd=lockfd,slot_identity=c.identity(os.fstat(lockfd)),unit=unit,nonce=a['nonce']))
  bus=Bus(unit)
  # Both actor creation and post-Popen binding are in this same finally scope.
  report['launch_attempts']=1
  launch=subprocess.Popen(command(a,args.admission_sha256),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,close_fds=True)
  try:report['systemd_run_exit']=launch.wait(timeout=5)
  except subprocess.TimeoutExpired:
   launch.kill();launch.wait();report['systemd_run_exit']='LAUNCH_TIMEOUT_RECONCILE_SAME_UNIT'
  # A failed/timed-out systemd-run may have already created the unit. Read it;
  # never blindly run systemd-run again and never assume no effect from rc.
  current=unit_props(unit,True)
  if current['LoadState']=='not-found':
   need(report['systemd_run_exit']==0,'LAUNCH_FAILED_NO_UNIT');need(False,'SUCCESS_LAUNCH_UNIT_MISSING')
  bound=scope(current,a,args.admission_sha256);cg=bind_cgroup(bound,op,unit,expected_cgroup)
  need(Path(cg).name==unit,'BOUND_CGROUP')
  if bound['MainPID']!='0':
   bound['_main_starttime']=Path('/proc',bound['MainPID'],'stat').read_text().rsplit(') ',1)[1].split()[19]
  bus.ref();report['bound_unit']=bound;report['bound_cgroup']=cg;report['unit_reference_acquired']=True
  origin=int(bound['ExecMainStartTimestampMonotonic'])/1e6;deadline=a['original_operation_start_monotonic']+lim['whole_wall_seconds']
  need(origin>=a['original_operation_start_monotonic'],'UNIT_START_BEFORE_ADMITTED_CLOCK')
  need(origin>=launch_start-1 and origin<=time.monotonic(),'LAUNCH_ORIGINAL_ORIGIN')
  report['state']='UNIT_RUNNING_SAME_OPERATION'
  while True:
   current=scope(unit_props(unit),a,args.admission_sha256,bound)
   if actual_exit(current) and kernel_empty(cg,unit,bound):break
   c.retention_snapshot(a['task_retention_root'],op)
   usage=0
   try:usage=int(dict(x.split() for x in Path(cg,'cpu.stat').read_text().splitlines())['usage_usec'])/1e6
   except FileNotFoundError:pass
   if pending or time.monotonic()>=deadline-lim['cleanup_reserve_seconds'] or usage+(time.process_time()-parent_cpu)+(children_cpu()-parent_children_cpu)>=lim['aggregate_CPU_seconds']-.25:raise TimeoutError('STOP_WITHIN_ORIGINAL_CLOCK')
   time.sleep(.05)
  report['unit_result_exit']=int(current['ExecMainStatus']);report['actual_exit_properties']=current
  report['state']='ROOT_FINITE_UNIT_CLOSED'
 except BaseException as error:
  report['state']='FAILED_OR_UNKNOWN_PRESERVED_NO_REPLAY';report['error_class']=type(error).__name__;report['reason_code']=str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z][A-Z0-9_]{0,120}',str(error)) else None
 finally:
  # Never let delivery/log/proof/BaseException bypass reconciliation of the
  # same actual launch and unit. Signals remain deferred until this is known.
  if launch is not None and launch.returncode is None:
   try:launch.kill();launch.wait(timeout=2)
   except BaseException as error:report['launcher_cleanup_error']=type(error).__name__
  if report['launch_attempts']:
   try:
    current=unit_props(unit,True)
    if current['LoadState']=='not-found':
     need(bound is None,'BOUND_UNIT_DISAPPEARED');need(not owned_actors(unit),'UNIT_ABSENT_ACTORS');closed=True
    else:
     # Bind even if launch->first property read/ref/save failed. Exact nonce,
     # ExecStart, boot, start origin and invocation gate the only stop target.
     current=scope(current,a,args.admission_sha256,bound)
     if bound is None:bound=current;cg=bind_cgroup(bound,op,unit,expected_cgroup)
     if bus is None:bus=Bus(unit)
     if not bus.held:bus.ref()
     report['bound_unit']=bound;report['bound_cgroup']=cg
     need(Path(cg).name==unit,'CLEANUP_BOUND_CGROUP')
     # Root may stop only this actual owned unit; KillMode closes its exact
     # namespace/process group. Permanent product units are never arguments.
     current=scope(unit_props(unit),a,args.admission_sha256,bound);need(no_job(current),'UNIT_JOB_PENDING')
     bus.stop_owned();report['same_bound_unit_stop_requested']=True
     cleanup_end=a['original_operation_start_monotonic']+lim['whole_wall_seconds']
     while time.monotonic()<cleanup_end:
      current=scope(unit_props(unit),a,args.admission_sha256,bound)
      if actual_exit(current) and current['ActiveState'] in ('inactive','failed') and kernel_empty(cg,unit,bound):
       closed=True;report['strict_closed_properties']=current;break
      time.sleep(.05)
     need(closed,'STRICT_CLOSURE_UNCONFIRMED')
     bus.release();report['reference_released_after_kernel_closure']=True
   except BaseException as error:
    report['closure_error_class']=type(error).__name__;report['state']='STOP_UNCONFIRMED_LOCK_HELD'
  else:closed=True
  report['actual_closure_observed']=closed
  report['elapsed_Root_parent_seconds']=time.monotonic()-launch_start;report['Root_parent_CPU_seconds']=time.process_time()-parent_cpu;report['Root_owned_helpers_CPU_seconds']=children_cpu()-parent_children_cpu
  finalprops=report.get('strict_closed_properties',{})
  if str(finalprops.get('CPUUsageNSec','')).isdecimal():
   report['whole_unit_accounted_CPU_seconds']=int(finalprops['CPUUsageNSec'])/1e9
   report['aggregate_unit_plus_parent_CPU_seconds']=report['whole_unit_accounted_CPU_seconds']+report['Root_parent_CPU_seconds']+report['Root_owned_helpers_CPU_seconds']
   if report['aggregate_unit_plus_parent_CPU_seconds']>lim['aggregate_CPU_seconds']:report['state']='AGGREGATE_CPU_EXCEEDED_PRESERVED'
  elif report['launch_attempts'] and closed:
   report['state']='FINAL_CPU_ACCOUNTING_INCONCLUSIVE_PRESERVED'
  try:report['final_retention']=c.retention_snapshot(a['task_retention_root'],op)
  except BaseException as error:report['retention_error_class']=type(error).__name__;report['state']='RETENTION_UNCONFIRMED_PRESERVED'
  report['original_operation_start_monotonic']=a['original_operation_start_monotonic'];report['original_whole_operation_deadline_monotonic']=a['original_operation_start_monotonic']+lim['whole_wall_seconds']
  report['completed_at_moscow']=c.utcmoscow();report['deferred_signals']=pending
  if op.exists():
   try:c.save(op/'ROOT-RESULT.json',report)
   except BaseException as error:report['result_save_error_class']=type(error).__name__
  if not closed:
   # No safe finite program can force an uninterruptible kernel actor or
   # unavailable manager to confirm closure. Keep this same visible parent and
   # lock alive for Root reconciliation; no new actors, stop or replay loop.
   # The protected ROOT-RESULT is the explicit blocker, not a false clean exit.
   print(json.dumps({'state':'STOP_UNCONFIRMED_LOCK_HELD','operation_key':key}),flush=True)
   while True:
    signal.pause()
  if bus is not None:bus.close()
  os.close(lockfd)
  for sig,handler in old.items():signal.signal(sig,handler)
 print(json.dumps({k:report[k] for k in ('state','actual_closure_observed','elapsed_Root_parent_seconds')}))
 return 0 if report['state']=='ROOT_FINITE_UNIT_CLOSED' and report.get('unit_result_exit')==0 else 1



def offline_check():
 c.safe_dir(B);pin,_=c.recipe_check()
 for path in B.glob('*.py'):compile(path.read_bytes(),str(path),'exec')
 template=c.decode(c.private(B/'verify-native-edits.ADMISSION.TEMPLATE.json',B)[0])
 need(template['state']=='UNBOUND_NOT_ADMITTED' and template['admitted_at_moscow']is None and template['slot_identity']is None and template['original_operation_start_monotonic']is None,'TEMPLATE_NOT_INERT')
 need(template['mode']==c.MODE and template['operation_key']is None and template['source_pins_sha256']is None,'TEMPLATE_NO_AUTHORITY')
 refs=c.decode(c.private(B/'REFERENCES.json',B)[0])
 codec_rows=[row for row in refs['files']if row.get('path')==str(c.CODEC_ACCEPTANCE_PATH)]
 need(len(codec_rows)==1,'CODEC_SOURCE_REFERENCE_REQUIRED');c.codec_acceptance(codec_rows[0])
 return dict(state='SOURCE_ONLY_NO_RUNTIME_AUTHORITY',source_pins_sha256=pin['sha256'],Office_starts=0,unit_starts=0,namespace_starts=0,secret_reads=0,codec_acceptance_sha256=c.CODEC_ACCEPTANCE_SHA,negative_observer_review='REQUIRED_FOR_FUTURE_EXECUTION_NOT_GRANTED_HERE')

def main():
 os.umask(0o077);p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--execute-once-root-accepted',action='store_true');p.add_argument('--admission',type=Path);p.add_argument('--admission-sha256');a=p.parse_args()
 need(a.check!=a.execute_once_root_accepted,'EXPLICIT_MODE')
 if a.check:print(json.dumps(offline_check()));return 0
 need(re.fullmatch('[0-9a-f]{64}',a.admission_sha256 or '') is not None,'ADMISSION_HASH_REQUIRED');return execute(a)
if __name__=='__main__':raise SystemExit(main())
