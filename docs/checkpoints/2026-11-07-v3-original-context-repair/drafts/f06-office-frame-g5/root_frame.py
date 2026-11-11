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
REVIEWED_CHANGED_FILES=['embedded_entry.py','f06_contract.py','inside_once.py','root_frame.py']
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

def retained_preflight(a,review):
 # This is one exact already-consumed operation, not a general migration or
 # permission to rerun it. Preserve its failed parent report and late closure.
 row=a['preflight_reconciliation']
 need(row==review.get('retained_preflight_reconciliation') and row['path']==str(B/'RETAINED-PREFLIGHT-ACCEPTANCE.json'),'RETAINED_PREFLIGHT_REVIEW_BINDING')
 raw,pin=c.private(row['path'],B);need(all(pin[k]==row[k] for k in ('bytes','sha256','identity')),'RETAINED_PREFLIGHT_ACCEPTANCE_PIN');reuse=json.loads(raw)
 need(reuse['schema']=='friday.f06.retained-preflight-reuse.v1' and reuse['state']=='ROOT_ACCEPTED_RETAINED_TYPED_PREFLIGHT_ONLY','RETAINED_PREFLIGHT_ACCEPTANCE')
 need(reuse['from_source_pins_sha256']==RETAINED_PREFLIGHT_PINS and reuse['to_source_pins_sha256']==a['source_pins_sha256'] and reuse['changed_source_files']==REVIEWED_CHANGED_FILES,'RETAINED_PREFLIGHT_SOURCE_MAPPING')
 need(reuse['preflight_reexecuted'] is False and reuse['original_window_PASS'] is False and reuse['full_application_PASS'] is False,'RETAINED_PREFLIGHT_HONEST_SCOPE')
 need(set(reuse['evidence'])==set(RETAINED_PREFLIGHT_FILES),'RETAINED_PREFLIGHT_EVIDENCE_SET')
 observed={};pins={}
 for name,(relative,sha) in RETAINED_PREFLIGHT_FILES.items():
  evidence=reuse['evidence'][name];path=RETAINED_PREFLIGHT_ROOT/relative
  need(evidence['path']==str(path),'RETAINED_PREFLIGHT_EXACT_PATH')
  raw,p=c.private(path,RETAINED_PREFLIGHT_ROOT)
  need(p['sha256']==sha and all(p[k]==evidence[k] for k in ('bytes','sha256','identity')),'RETAINED_PREFLIGHT_EVIDENCE_PIN')
  observed[name]=json.loads(raw);pins[name]=p
 need(a['preflight_result']==pins['root_result'] and a['preflight_typed_proof']==pins['typed_proof'],'RETAINED_PREFLIGHT_ADMISSION_JOIN')
 old=observed['source_pins'];current=json.loads(c.private(B/'SOURCE-PINS.json',B)[0])
 oldfiles={r['name']:r for r in old['files']};newfiles={r['name']:r for r in current['files']}
 need(set(oldfiles)==set(newfiles) and sorted(k for k in oldfiles if oldfiles[k]!=newfiles[k])==REVIEWED_CHANGED_FILES,'RETAINED_PREFLIGHT_EXACT_REVIEWED_SOURCE_DELTA')
 admission=observed['admission'];original=observed['root_result'];unit=observed['unit_result'];inside=observed['inside_result'];typed=observed['typed_proof'];parent=observed['parent_binding'];closure=observed['unit_closure'];final=observed['parent_closure'];bound=original['bound_unit']
 need(admission['assignment']==c.ASSIGNMENT and admission['state']=='ROOT_FRESH_ONCE_ADMITTED' and admission['mode']=='preflight' and admission['operation_key']=='preflight-g1' and admission['source_pins_sha256']==RETAINED_PREFLIGHT_PINS and admission['limits']==c.limits('preflight'),'RETAINED_PREFLIGHT_ORIGINAL_ADMISSION')
 need(original['state']=='STOP_UNCONFIRMED_LOCK_HELD' and original['reason_code']=='UNIT_BIRTH_SCOPE_CHANGED' and original['actual_closure_observed'] is False and original['launch_attempts']==1 and original['systemd_run_exit']==0,'RETAINED_PREFLIGHT_ORIGINAL_OBSERVATION')
 need(original['source_pins_sha256']==RETAINED_PREFLIGHT_PINS and original['admission']==pins['admission'] and original['boot_id']==admission['boot_id']==parent['boot_id']==a['boot_id'] and admission['uid']==parent['root_uid']==a['uid'],'RETAINED_PREFLIGHT_BOOT_UID_SOURCE_JOIN')
 expected_unit=c.unit_name('preflight-g1');origin=bound['ExecMainStartTimestampMonotonic'];identity={k:bound[k] for k in ('Id','InvocationID','Description','ExecMainStartTimestampMonotonic')}
 need(bound['Id']==original['unit']==unit['unit']==parent['unit']==expected_unit and bound['Description']=='FRW F06 once '+admission['nonce'] and parent['nonce']==admission['nonce'] and parent['admission_sha256']==pins['admission']['sha256'],'RETAINED_PREFLIGHT_UNIT_NONCE_JOIN')
 need(unit['state']=='FINITE_UNIT_CONSUMER_FINISHED_ORACLE_RESULT_SEPARATE' and unit['mode']=='preflight' and unit['operation_key']=='preflight-g1' and unit['namespace_closed'] is True and unit['namespace_exit']==0 and abs(unit['original_unit_start_monotonic']-int(origin)/1e6)<.000002 and unit['cgroup']==original['bound_cgroup'],'RETAINED_PREFLIGHT_CONSUMER_JOIN')
 need(0<unit['elapsed_whole_unit_seconds']<=30 and 0<=unit['whole_cgroup_CPU_seconds']<=20,'RETAINED_PREFLIGHT_CONSUMER_LIMITS')
 need(inside['state']=='ISOLATED_UNO_PREFLIGHT_NO_OFFICE_PASS' and inside['mode']=='preflight' and inside['Office_starts']==0 and inside['client_starts']==1 and inside['owned_children_closed'] is True and inside['client_exit']==0 and inside['cleanup_errors']==[],'RETAINED_PREFLIGHT_INSIDE_PROOF')
 need(typed['state']=='ISOLATED_EMBEDDED_UNO_TYPES_IMPORT_PASS_NO_OFFICE' and typed['Office_starts']==0 and typed['document_loads']==0 and typed['secret_reads']==0 and inside['client_birth']=={k:typed[k] for k in ('pid','starttime')},'RETAINED_PREFLIGHT_TYPED_NAMESPACE_JOIN')
 need(closure['schema']=='friday.f06.Root-actual-postexit-reconciliation.v1' and closure['state']=='ROOT_EXACT_EXISTING_PREFLIGHT_UNIT_CLOSED_AFTER_CHECKER_FALSE_REFUSAL' and closure['original_root_result']==pins['root_result'] and closure['bound_unit_identity']==identity,'RETAINED_PREFLIGHT_CLOSURE_JOIN')
 legacy_argv=['/usr/bin/python3','-I','-B','-S',str(RETAINED_PREFLIGHT_ROOT/'run_once.py'),'--admission',str(RETAINED_PREFLIGHT_ROOT/'preflight-g1.ADMISSION.json'),'--admission-sha256',pins['admission']['sha256']]
 execstart_identity(bound['ExecStart'],legacy_argv)
 for terminal in (closure['actual_before_stop'],closure['actual_after_stop']):
  need(all(terminal[k]==identity[k] for k in identity) and actual_exit(terminal) and terminal['ExecMainStatus']=='0' and no_job(terminal),'RETAINED_PREFLIGHT_TERMINAL_IDENTITY')
  execstart_identity(terminal['ExecStart'],legacy_argv)
 need(closure['actual_after_stop']['ActiveState']=='inactive' and closure['actual_kernel_members']==[] and closure['owned_actors']==[] and closure['same_unit_only_stop'] is True and closure['preflight_reexecuted'] is False and closure['original_30s_not_reset'] is True and closure['late_closure_readback_not_original_window_PASS'] is True and closure['actual_flock_held_until_closure'] is True and closure['namespace_exit']==0 and closure['actual_Office_starts']==0 and closure['documents_or_credentials_read'] is False,'RETAINED_PREFLIGHT_LATE_CLOSURE')
 need(closure['parent_pid']==parent['root_pid']==final['parent_pid'] and closure['parent_starttime']==parent['root_starttime'] and final['state']=='EXACT_PREFLIGHT_PARENT_REAPED_AND_SHARED_SLOT_FREE' and final['parent_absent'] is True and final['shared_slot_reacquired_and_released'] is True and final['same_unit_actors']==[] and final['operation_reexecuted'] is False,'RETAINED_PREFLIGHT_PARENT_SLOT_CLOSURE')
 return reuse

MISSING_STAGE_ROOT=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-PIPE-OBSERVER-FIX-20261111')
MISSING_STAGE_PRIOR_SOURCE='6cbe587b02b0dfec40a7fb1111aa373a768a96351cda8b69e9ffa68310893f75'
MISSING_STAGE_CLOSURE_SHA='d3f96a917c78b3e82c8b297ad263a88b04dce7cca480d747404c97395fd0ebf1'
MISSING_STAGE_FILES={'ROOT-RESULT.json': '88bfa1b837bafa8556fbb1702c7f75fb990b4a4fcb89516a56475391aa0451d0', 'UNIT-RESULT.json': '6c9253bc7ae69d9c7e36d4734f9dd49380ab3b29e121917b8247cc0123f73d55', 'PARENT-BINDING.json': 'f5e99a7cf0e258395831b16086cf3a9eca31fe48b2a13cabf861b39fd584e5ab', 'work/INSIDE-RESULT.json': 'f96f86e56415c3286bece2e02961e43afcd16af4429292b9744c031782a16e9f', 'work/attempt-2/CLIENT-READY.json': '2ac8e3248e86e8346d2ebd6a4e3ecb8b165f8392554b0ec0b6f8bbf60ec54597', 'work/attempt-2/PIPE-OBSERVATION.json': '7d16339842e6c55302a454246fb6090ca05484036b8cbbd27f54803216d91275', 'work/attempt-2/PIPE-OWNERSHIP-ACCEPTED.json': '76309741d14faac5ac4a59e64f4364935ea107bbd045020752e04835b4fa4d35', 'work/attempt-2/PRODUCER-ENTERED.json': '96daa440eb36ee039f8c0031e81b6e8c1832f72b7c1662bf704481c9d4d6d946', 'work/attempt-2/client.stdout.private': 'f687e298652364015e08992984dbd06b706f51bce9193c4f3886a03475ef114c'}
PRODUCER_CONTEXT_CHANGED_FILES=['embedded_entry.py','f06_contract.py','root_frame.py']
LOADER_COMPARISON_ROOT=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/F06-PRODUCER-LOADER-COMPARISON-ONCE')
LOADER_COMPARISON_SHA='c93b0667a9230f139385ed1d25b8437d7d6496c017df5629190294efa0946750'
LOADER_COMPARISON_CLOSURE_SHA='ab05838cee4196355c53826441dc374c14997917de8e6103872d3ffafa7f68ae'
BOOTSTRAP_POLICY=dict(profile='fresh_factory_private',max_Office_starts=3,max_successfully_connected_producers=1,continuation_only_after_actual_wait81=True,continuation_before_any_CLIENT_READY=True,prior_both_children_reaped=True,prior_owned_pipe_closed=True,same_original_absolute_operation_deadline=True,actual_zero_components_before_producer=True,own_endpoint_parent_accept_before_producer=True,old_g2_Office_exit='NOT_RECORDED_BY_OLD_OBSERVER',generic_further_generation=False)

def missing_document_stage(a,review):
 # Exact Root-selected new operation after proved context repair. G4 really
 # entered the producer; only its seven document jobs remain unperformed.
 need(a['mode']=='generate' and a['operation_key']=='generate-g5','MISSING_STAGE_EXACT_OPERATION')
 row=a['missing_stage_authority']
 need(row==review.get('missing_stage_authority') and row['path']==str(B/'MISSING-DOCUMENT-STAGE-AUTHORITY.json'),'MISSING_STAGE_REVIEW_BINDING')
 raw,pin=c.private(row['path'],B);need(all(pin[k]==row[k] for k in ('bytes','sha256','identity')),'MISSING_STAGE_AUTHORITY_PIN');authority=json.loads(raw)
 need(authority['schema']=='friday.f06.Root-producer-context-missing-document-authority.v1' and authority['state']=='ROOT_ACCEPTED_EXACT_PRODUCER_CONTEXT_FIX_MISSING_DOCUMENT_STAGE_ONLY','MISSING_STAGE_AUTHORITY')
 need(authority['prior_source_pins_sha256']==MISSING_STAGE_PRIOR_SOURCE and authority['new_source_pins_sha256']==a['source_pins_sha256'] and authority['changed_source_files']==PRODUCER_CONTEXT_CHANGED_FILES,'MISSING_STAGE_SOURCE_MAPPING')
 need(authority['prior_operation_key']=='generate-g4' and authority['new_operation_key']==a['operation_key'] and authority['new_unit']==c.unit_name(a['operation_key']) and authority['limits']==c.LIMITS,'MISSING_STAGE_UNIT_LIMITS')
 need(authority['bootstrap_policy']==BOOTSTRAP_POLICY and authority['producer_execution_context']==dict(run_name='f06_producer_library',preserve_existing_main_module=True,explicit_main_call_once=True,unchanged_producer_sha256='795812f55fc8324b10a3810befad53b8ac3f932f924e6d45a59b690fe145bb8e'),'MISSING_STAGE_EXACT_EXECUTION_CONTEXT')
 need(authority['original_operation_replay'] is False and authority['original_clocks_reset'] is False and authority['preflight_reexecuted'] is False and authority['prior_failure_preserved'] is True and authority['remaining_document_count']==7 and authority['remaining_stores']==7 and authority['remaining_password_probes']==21,'MISSING_STAGE_SCOPE')
 need(authority['g4_producer_entered'] is True and authority['g4_credential_read_status']=='MAY_HAVE_BEEN_READ' and authority['g4_original_exception_location']=='NOT_RECORDED_BY_ORIGINAL_WRAPPER' and authority['old_g2_Office_exit']=='NOT_RECORDED_BY_OLD_OBSERVER','MISSING_STAGE_HONEST_PRIOR_FACTS')
 evidence_specs=(('prior_source_pins',MISSING_STAGE_ROOT/'SOURCE-PINS.json',MISSING_STAGE_ROOT,MISSING_STAGE_PRIOR_SOURCE),('zero_document_closure',MISSING_STAGE_ROOT/'operations/generate-g4/ROOT-G4-ZERO-DOCUMENT-STAGE-AND-CLOSURE.json',MISSING_STAGE_ROOT,MISSING_STAGE_CLOSURE_SHA),('loader_comparison',LOADER_COMPARISON_ROOT/'work/LOADER-COMPARISON.json',LOADER_COMPARISON_ROOT,LOADER_COMPARISON_SHA),('loader_comparison_closure',LOADER_COMPARISON_ROOT/'ROOT-RESULT.json',LOADER_COMPARISON_ROOT,LOADER_COMPARISON_CLOSURE_SHA))
 need(set(authority['evidence'])=={r[0] for r in evidence_specs},'MISSING_STAGE_EVIDENCE_SET');observed={}
 for name,path,root,sha in evidence_specs:
  row=authority['evidence'][name];need(row['path']==str(path),'MISSING_STAGE_EXACT_EVIDENCE_PATH')
  raw,p=c.private(path,root);need(p['sha256']==sha and all(p[k]==row[k] for k in ('bytes','sha256','identity')),'MISSING_STAGE_EVIDENCE_PIN');observed[name]=json.loads(raw)
 oldfiles={r['name']:r for r in observed['prior_source_pins']['files']};newfiles={r['name']:r for r in json.loads(c.private(B/'SOURCE-PINS.json',B)[0])['files']}
 need(set(oldfiles)==set(newfiles) and sorted(k for k in oldfiles if oldfiles[k]!=newfiles[k])==PRODUCER_CONTEXT_CHANGED_FILES,'MISSING_STAGE_EXACT_REVIEWED_SOURCE_DELTA')
 closure=observed['zero_document_closure']
 need(closure['schema']=='friday.f06.Root-g4-zero-document-stage-custody.v1' and closure['state']=='GENERATION_G4_CLOSED_AFTER_OWNERSHIP_AND_PRODUCER_ENTRY_SYSTEMERROR_BEFORE_DOCUMENT_DIRECTORY' and closure['original_source_pins_sha256']==MISSING_STAGE_PRIOR_SOURCE,'MISSING_STAGE_CLOSURE_SCHEMA')
 need(closure['actual_root_parent_absent'] is True and closure['actual_unit_actors']==[] and closure['actual_shared_slot_reacquired_and_released'] is True and closure['original_operation_replay'] is False and closure['original_clocks_reset'] is False,'MISSING_STAGE_KNOWN_CLOSURE')
 need(closure['Office_starts_consumed']==closure['client_starts_consumed']==2 and closure['actual_first_natural_Office_exit']==81 and closure['actual_second_Office_cleanup_exit']==-9 and closure['actual_second_client_exit']==2,'MISSING_STAGE_ACTUAL_G4_EXITS')
 need(closure['actual_empty_component_count']==0 and closure['actual_pipe_listener_count']==closure['actual_pipe_connected_count']==1 and closure['producer_permissions']==1 and closure['producer_entered'] is True and closure['producer_exception_class']=='SystemError' and closure['producer_original_exception_location']=='NOT_RECORDED_BY_ORIGINAL_WRAPPER','MISSING_STAGE_ACTUAL_G4_PRODUCER_ENTRY')
 need(all(closure[k]==0 for k in ('Office_input_document_loads','encrypted_stores','password_probes')) and closure['encrypted_output_directory_absent'] is True,'MISSING_STAGE_ZERO_DOCUMENT_CUSTODY')
 for field,name in (('context_comparison','loader_comparison'),('context_comparison_root_closure','loader_comparison_closure')):
  need(all(closure[field][k]==authority['evidence'][name][k] for k in ('path','bytes','sha256')),'MISSING_STAGE_CAUSAL_EVIDENCE_JOIN')
 need(set(closure['evidence'])==set(MISSING_STAGE_FILES),'MISSING_STAGE_CLOSED_EVIDENCE_SET');reports={}
 for relative,sha in MISSING_STAGE_FILES.items():
  row=closure['evidence'][relative];need(row['path']==str(MISSING_STAGE_ROOT/'operations/generate-g4'/relative),'MISSING_STAGE_CLOSED_EXACT_PATH')
  raw,p=c.private(row['path'],MISSING_STAGE_ROOT);need(p['sha256']==sha and all(p[k]==row[k] for k in ('bytes','sha256','identity')),'MISSING_STAGE_CLOSED_EVIDENCE_PIN');reports[relative]=json.loads(raw)
 root=reports['ROOT-RESULT.json'];unit=reports['UNIT-RESULT.json'];inside=reports['work/INSIDE-RESULT.json'];parent=reports['PARENT-BINDING.json'];ready=reports['work/attempt-2/CLIENT-READY.json']
 need(root['state']=='ROOT_FINITE_UNIT_CLOSED' and root['actual_closure_observed'] is True and root['unit_result_exit']==1 and root['source_pins_sha256']==MISSING_STAGE_PRIOR_SOURCE and root['launch_attempts']==1,'MISSING_STAGE_ROOT_CLOSED_FAILURE')
 need(root['operation_key']==unit['operation_key']=='generate-g4' and root['mode']==unit['mode']==inside['mode']=='generate' and root['unit']==unit['unit']==parent['unit']==c.unit_name('generate-g4') and root['boot_id']==parent['boot_id']==a['boot_id'] and parent['root_uid']==a['uid'],'MISSING_STAGE_OLD_OPERATION_JOIN')
 need(unit['namespace_closed'] is True and unit['namespace_exit']==1 and unit['reason_code']=='NAMESPACE_TERMINAL_NONZERO' and abs(unit['original_unit_start_monotonic']-int(root['bound_unit']['ExecMainStartTimestampMonotonic'])/1e6)<.000002 and unit['cgroup']==root['bound_cgroup'],'MISSING_STAGE_NAMESPACE_JOIN')
 need(inside['Office_starts']==inside['client_starts']==2 and inside['producer_permissions']==1 and inside['owned_children_closed'] is True and inside['owned_pipes_closed'] is True and inside['cleanup_errors']==[],'MISSING_STAGE_INSIDE_CLOSED_FAILURE')
 need(len(inside['attempts'])==2,'MISSING_STAGE_TWO_ACTUAL_ATTEMPTS');first,second=inside['attempts']
 need(first['Office_exit']==81 and first['Office_exit_observed_by_wait'] is True and first['Office_terminal_before_cleanup'] is True and first['client_ready'] is False and first['matching_socket_files']==[],'MISSING_STAGE_FIRST_ACTUAL_WAIT81')
 need(second['Office_exit']==-9 and second['client_exit']==2 and second['Office_exit_observed_by_wait'] is True and second['client_exit_observed_by_wait'] is True and second['client_ready'] is True and second['pipe_accepted'] is True and second['producer_entered'] is True,'MISSING_STAGE_SECOND_ACTUAL_ENTRY_ERROR')
 need(all(r['owned_children_closed'] is True and r['owned_pipe_closed'] is True and not r['document_phase_exists'] for r in (first,second)),'MISSING_STAGE_ATTEMPT_ZERO_DOCUMENTS_CLOSED')
 need(ready['state']=='CONNECTED_ZERO_COMPONENTS_NO_DOCUMENT_OR_SECRET' and type(ready['component_count']) is int and ready['component_count']==0 and ready['pipe']==second['pipe'] and ready['pid']==second['client_birth']['pid'] and ready['starttime']==second['client_birth']['starttime'],'MISSING_STAGE_ACTUAL_READY_ZERO_COMPONENTS_JOIN')
 entered=reports['work/attempt-2/PRODUCER-ENTERED.json'];need(entered['pipe']==ready['pipe'] and entered['pid']==ready['pid'] and entered['document_loads_yet']==0,'MISSING_STAGE_ACTUAL_PRODUCER_MARKER')
 need(reports['work/attempt-2/client.stdout.private']==dict(status='ERROR',exception_class='SystemError'),'MISSING_STAGE_ORIGINAL_ERROR_CLASS_ONLY')
 contrast=observed['loader_comparison'];good,bad=contrast['rows']
 need(good==dict(style='custom_module_direct_main',status='PREFIX_PASS_NO_DOCUMENT_LOGIC') and bad['style']=='runpy___main__' and bad['status']=='PREFIX_EXCEPTION' and bad['exception_class']=='SystemError','MISSING_STAGE_CONTROLLED_LOADER_CONTRAST')
 need(dict(file='/recipe/producer_prefix.py',line=89,function='main') in bad['frames'] and dict(file='/opt/friday-document-toolchain/root/usr/lib/libreoffice/program/uno.py',line=373,function='_uno_import') in bad['frames'] and contrast['source_boundary']=='outassignment/mkdir and alljobs excluded' and contrast['documents']==contrast['stores']==0 and contrast['messages_and_locals_saved'] is False,'MISSING_STAGE_CONTROLLED_PREFIX_LOCATION')
 closed=observed['loader_comparison_closure']
 need(closed['state']=='DISTINCT_PREFIX_LOADER_COMPARISON_KNOWN_CLOSED_NO_DOCUMENTS' and closed['original_producer_sha256']=='795812f55fc8324b10a3810befad53b8ac3f932f924e6d45a59b690fe145bb8e' and closed['original_stop_before_line']==165 and closed['owned_children_and_pipes_closed'] is True and closed['original_generations_replayed'] is False and closed['no_document_or_store_code_in_prefix'] is True,'MISSING_STAGE_CONTROLLED_CONTRAST_KNOWN_CLOSED')
 return authority

def validate_admission(path,sha):
 raw,pin=c.private(path,B);need(pin['sha256']==sha,'ADMISSION_SHA');a=json.loads(raw)
 mode=a['mode'];key=a['operation_key'];c.operation(key,mode);lim=c.limits(mode)
 need(mode!='preflight','PREFLIGHT_ALREADY_CONSUMED_RECONCILE_ONLY')
 need(path==B/(key+'.ADMISSION.json') and a['state']=='ROOT_FRESH_ONCE_ADMITTED' and a['assignment']==c.ASSIGNMENT,'ADMISSION_STATE_PATH')
 need(a['source_pins_sha256']==c.recipe_check()[0]['sha256'] and a['limits']==lim,'ADMISSION_SOURCE_LIMITS')
 need(a['uid']==os.getuid() and a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip() and re.fullmatch('[0-9a-f]{32}',a['nonce']) is not None,'ADMISSION_UID_BOOT_NONCE')
 at=datetime.datetime.fromisoformat(a['admitted_at_moscow']);age=(datetime.datetime.now(datetime.timezone.utc)-at).total_seconds();need(at.utcoffset()==datetime.timedelta(hours=3) and 0<=age<=120,'ADMISSION_FRESH_TIME')
 cpus=a['actual_two_cpu_ids'];need(len(cpus)==2 and len(set(cpus))==2 and all(type(x) is int for x in cpus) and set(cpus)<=os.sched_getaffinity(0),'ACTUAL_CPU_AFFINITY')
 review,_=proof(a['source_review']);need(review['state']=='ROOT_ACCEPTED_F06_SOURCE_DELTA' and review['source_pins_sha256']==a['source_pins_sha256'] and review['findings_remaining']==[] and review['producer_verify_inputs_reviewed'] is True,'SOURCE_REVIEW')
 if mode=='generate':missing_document_stage(a,review)
 fresh,_=proof(a['fresh_boundary']);need(fresh['state']=='ROOT_FRESH_F06_KERNEL_CUSTODY' and fresh['boot_id']==a['boot_id'] and fresh['uid']==os.getuid() and fresh['slot_identity']==a['slot_identity'],'ROOT_FRESH_PROOF')
 fat=datetime.datetime.fromisoformat(fresh['observed_at_moscow']);need(0<=(datetime.datetime.now(datetime.timezone.utc)-fat).total_seconds()<=120,'BOUNDARY_FRESH_TIME')
 need(fresh['bank']==c.bank_snapshot(),'FRESH_BANK_METADATA_CAS_CRITICAL4')
 need(fresh['affinity_cpu_ids']==sorted(os.sched_getaffinity(0)) and fresh['memory_available_kib']>=3*1024*1024 and fresh['CPU_pressure_raw'] and fresh['IO_pressure_raw'],'ROOT_RESOURCE_OBSERVATIONS')
 mem=dict((x.split(':',1)[0],x.split(':',1)[1].strip()) for x in Path('/proc/meminfo').read_text().splitlines());need(int(mem['MemAvailable'].split()[0])>=3*1024*1024,'CURRENT_MEMORY_AVAILABLE')
 if mode!='preflight':
  retained_preflight(a,review)
  c.plain_inputs()
 if mode=='verify-inputs':
  raw,p=c.private(a['reconciled_manifest']['path'],B);need(all(p[k]==a['reconciled_manifest'][k] for k in ('bytes','sha256','identity')),'RECONCILED_MANIFEST_PIN');c.reconciled_inputs(raw,p)
 return a,pin

def acquire_slot(a):
 need(str(c.SLOT)==a['slot_path'],'SLOT_EXACT_PATH')
 for parent in c.SLOT.parents:need(not parent.is_symlink(),'SLOT_PARENT_LINK')
 fd=os.open(c.SLOT,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  s=os.fstat(fd);need(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o600 and s.st_nlink==1 and s.st_size==0,'SLOT_CUSTODY')
  need(c.identity(s)==a['slot_identity']==c.identity(c.SLOT.lstat()),'FRESH_SLOT_IDENTITY')
  fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);need(c.identity(os.fstat(fd))==c.identity(c.SLOT.lstat()),'LOCKED_SLOT_CAS');return fd
 except BaseException:os.close(fd);raise

def execute(args):
 need(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'ROOT_INTERPRETER_FLAGS')
 a,ap=validate_admission(args.admission,args.admission_sha256);mode=a['mode'];lim=c.limits(mode);key=a['operation_key'];op=c.operation(key,mode);unit=c.unit_name(key)
 c.safe_dir(B);need(not os.path.lexists(op),'OPERATION_NO_REPLAY')
 ops=B/'operations'
 if not ops.exists():ops.mkdir(mode=0o700)
 c.safe_dir(ops);lockfd=acquire_slot(a);bus=None;launch=None;bound=None;cg=None;closed=False;pending=[]
 report=dict(state='PRELAUNCH_REFUSAL',mode=mode,operation_key=key,unit=unit,boot_id=a['boot_id'],source_pins_sha256=a['source_pins_sha256'],admission=ap,started_at_moscow=c.utcmoscow(),actual_closure_observed=False,launch_attempts=0)
 old={}
 def defer(sig,_):pending.append(sig)
 for sig in (signal.SIGINT,signal.SIGTERM):old[sig]=signal.signal(sig,defer)
 launch_start=time.monotonic();parent_cpu=time.process_time();parent_children_cpu=children_cpu();expected_cgroup=None
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
  origin=int(bound['ExecMainStartTimestampMonotonic'])/1e6;deadline=origin+lim['whole_wall_seconds']
  need(origin>=launch_start-1 and origin<=time.monotonic(),'LAUNCH_ORIGINAL_ORIGIN')
  report['state']='UNIT_RUNNING_SAME_OPERATION'
  while True:
   current=scope(unit_props(unit),a,args.admission_sha256,bound)
   if actual_exit(current) and kernel_empty(cg,unit,bound):break
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
     cleanup_end=launch_start+lim['whole_wall_seconds']
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
 c.safe_dir(B);pin,_=c.recipe_check();c.plain_inputs()
 for path in B.glob('*.py'):compile(path.read_bytes(),str(path),'exec')
 for mode in ('preflight','generate','verify-inputs'):
  a=json.loads(c.stable(B/(mode+'.ADMISSION.TEMPLATE.json'))[0]);need(a['state']=='UNBOUND_NOT_ADMITTED' and a['admitted_at_moscow'] is None and a['slot_identity'] is None,'TEMPLATE_NOT_INERT')
 return dict(state='SOURCE_ONLY_NO_RUNTIME_AUTHORITY',source_pins_sha256=pin['sha256'],Office_starts=0,unit_starts=0,namespace_starts=0,secret_reads=0)

def main():
 os.umask(0o077);p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--execute-once-root-accepted',action='store_true');p.add_argument('--admission',type=Path);p.add_argument('--admission-sha256');a=p.parse_args()
 need(a.check!=a.execute_once_root_accepted,'EXPLICIT_MODE')
 if a.check:print(json.dumps(offline_check()));return 0
 need(re.fullmatch('[0-9a-f]{64}',a.admission_sha256 or '') is not None,'ADMISSION_HASH_REQUIRED');return execute(a)
if __name__=='__main__':raise SystemExit(main())
