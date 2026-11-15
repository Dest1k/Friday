"""Independent Root delta controls, pure synthetic observations only."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import copy,hashlib,json,os,runpy,stat,struct,types

Q=Path(__file__).resolve().parent
S=Path('/home/jericho/.cache/FRW-ASTRA-CALC-GPGME-ENGINE-INIT-GUARD-SOURCE-20261115')
V=Path('/home/jericho/.cache/FRW-ASTRA-CALC-GPGME-M1-SOURCE-REVIEW-20261115')
def ref(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
assert ref(V/'RESULT.json')['sha256']=='5ceaf8637e68243d5721b3d7bb173c3151910a33e77e790607105f99fd28cb2f'
assert ref(V/'repair-copy/gpgme_engine_policy.py')['sha256']=='a21ec131a93c99948a1d41cbce0f67b4e5ec0540de69fc8389a003df103bd84f'
assert ref(V/'repair-copy/gpgme_mapped_image.py')['sha256']=='54b43435a2e788a970bbbe54b1383e1b459b9de22d2b8830efe5bd6acefcebd1'
p=types.SimpleNamespace(**runpy.run_path(str(V/'repair-copy/gpgme_engine_policy.py')))
m=types.SimpleNamespace(**runpy.run_path(str(V/'repair-copy/gpgme_mapped_image.py')))
checks=[]
def passed(name):checks.append({'name':name,'state':'PASS_SOURCE_ONLY'})
def refused(name,fn):
    try:fn()
    except RuntimeError as exc:
        passed(name);return str(exc)
    raise AssertionError(name+'_unexpectedly_accepted')

env=dict(p.ISOLATED)
p.validate_environment(env,env);passed('unset_data_home_uses_isolated_home')
for value in ['/home/hostuser/data','/tmp/friday-metric-work/data-other','/tmp/friday-metric-work/../data']:
    bad=dict(env,XDG_DATA_HOME=value)
    refused('unsafe_data_home_'+str(len(checks)),lambda:p.validate_environment(bad,bad))
safe=dict(env,XDG_DATA_HOME='/tmp/friday-metric-work/data');p.validate_environment(safe,safe);passed('exact_private_data_home')

original=dict(pid=21,ppid=11,start_ticks=101)
reaper=dict(pid=1,ppid=0,start_ticks=10)
operation=dict(operation_id='ROOT_PURE_SOURCE_DELTA',nonce='4'*32,deadline_monotonic=240.0)
context=dict(operation,now=2.0,original=original,all_stop=True,phase='LOAD_OPEN',records_count=0,
    metric_active=False,library_current_bound=True,environment_current_bound=True,
    configuration_isolated=True,resource_custody_bound=True)
profile=json.loads((S/'GPGME-ENGINE-INIT-SOURCE-PROFILE.json').read_text())
helpers={r:dict(path='/owned-root-fixture/'+r,sha256=hashlib.sha256(r.encode()).hexdigest(),dev=2050,ino=i+20)
    for i,r in enumerate(('gpgconf','gpg','gpgsm','g13'))}
readfd=dict(dev=15,ino=80,type=stat.S_IFIFO,rdev=0,access=0,cloexec=True)
writefd=dict(readfd,access=1)
null=dict(dev=1,ino=3,type=stat.S_IFCHR,rdev=259,access=2,cloexec=False)
fds={0:null,1:dict(writefd,cloexec=False),2:dict(null)}
intermediate=dict(pid=40,ppid=21,start_ticks=201)
final=dict(pid=41,ppid=40,start_ticks=202)
adopted=dict(final,ppid=1)
thread=[21,32,0]
def machine():
    c=p.EngineInitPreparation(profile,original,operation,env,source_mode='FALLBACK_OR_CACHED',helpers=helpers,reaper=reaper)
    c.arm(context,'gpg_version',thread,[helpers['gpg']['path'],'--version'],helpers['gpg'],readfd,writefd,source_route='gpg_version')
    c.birth(context,original,intermediate,4,event='fork',return_offset=p.FIRST_FORK_RETURN,thread=thread)
    return c
def second(c):c.birth(context,intermediate,final,5,event='fork',return_offset=p.SECOND_FORK_RETURN,thread=[40,40,0])
c=machine();first=refused('intermediate_cannot_exit_before_second_birth',lambda:c.exit(context,intermediate,4,0,absent=True))
assert refused('first_refusal_remains_terminal',lambda:second(c))==first
c=machine();second(c);c.exit(context,intermediate,4,0,absent=True);c.spawn_return(context,thread,0)
refused('read_terminal_requires_exec_entry',lambda:c.pipe_terminal(context,thread,c.current['pipe'],read_closed=True,terminal='OBSERVED_NEWLINE_THEN_READ_CLOSE'))
c=machine();second(c);c.exit(context,intermediate,4,0,absent=True);c.spawn_return(context,thread,0)
c.reparent(context,adopted,exact_reaper_identity=reaper,old_parent_absent=True)
c.exec_before_execution(context,adopted,helpers['gpg'],[helpers['gpg']['path'],'--version',],fds,env,null_rdev=259,event='exec_before_first_instruction')
c.entry(context,adopted,image_and_exact_dependency_set_bound=True)
c.exit(context,adopted,5,0,absent=True)
c.pipe_terminal(context,thread,c.current['pipe'],read_closed=True,terminal='OBSERVED_NEWLINE_THEN_READ_CLOSE')
c.close_invocation(context,no_writer_or_other_descendant=True,pipe_read_end_absent=True)
c.finish_initialization(context,exact_engine_info_return=True,known_no_more_spawn=True)
assert c.snapshot()['source_protocol_closed'] is True and c.snapshot()['runtime_attested'] is False
passed('positive_spawn_return_before_exec_with_explicit_reparent_and_writer_exit_before_readclose')
refused('M1_runtime_phase_still_rejected',lambda:p.runtime_phase_gate(profile))

# Independent two-load synthetic ELF; never written or executed as a target.
raw=bytearray(8192);ident=b'\x7fELF\x02\x01\x01'+bytes(9)
struct.pack_into('<16sHHIQQQIHHHHHH',raw,0,ident,3,62,1,0,64,0,0,64,56,3,0,0,0)
for n,ph in enumerate([(1,5,0,0,0,4096,4096,4096),(1,6,4096,4096,4096,4096,8192,4096),(4,4,512,512,512,36,36,4)]):
    struct.pack_into('<IIQQQQQQ',raw,64+n*56,*ph)
bid=bytes(range(20));struct.pack_into('<III',raw,512,4,len(bid),3);raw[524:528]=b'GNU\0';raw[528:548]=bid;raw=bytes(raw)
image=dict(path='/usr/lib/owned-root-fixture.so',sha256=hashlib.sha256(raw).hexdigest(),build_id=bid.hex())
stamp=dict(dev_major=8,dev_minor=2,ino=42,size=len(raw),mtime_ns=123,ctime_ns=124,mode=stat.S_IFREG|0o644,uid=0,nlink=1)
maps=('400000-401000 r-xp 00000000 08:02 42 '+image['path']+'\n401000-402000 rw-p 00001000 08:02 42 '+image['path']+'\nffffffffff600000-ffffffffff601000 --xp 00000000 00:00 0 [vsyscall]\n').encode()
def bind(before=maps,after=maps,last=None):return m.bind_current_image(before,after,stamp,stamp if last is None else last,raw,image,0x400100)
result=bind();assert result['relative_pc']==0x100 and result['collector_complete'] is False and result['runtime_attested'] is False
passed('positive_RX_RW_ELF_join_with_unsigned_vsyscall_not_runtime')
relro=maps.replace(b'rw-p',b'r--p');m.bind_current_image(relro,relro,stamp,stamp,raw,image,0x400100);passed('RELRO_permission_narrowing_preserved')
for name,bad in [('WX_text',maps.replace(b'r-xp',b'rwxp')),('unaligned_file_offset',maps.replace(b'00001000',b'00001001'))]:
    refused(name,lambda bad=bad:bind(bad,bad))
refused('after_stamp_bool_not_integer_CAS',lambda:bind(last=dict(stamp,nlink=True)))
refused('bytearray_after_not_exact_bytes',lambda:bind(after=bytearray(maps)))
refused('namespace_overflow_owner_not_host_root',lambda:m.bind_current_image(maps,maps,dict(stamp,uid=65534),dict(stamp,uid=65534),raw,image,0x400100))
host=Path('/usr/lib/x86_64-linux-gnu/libgpgme.so.45.0.1').read_bytes()
assert hashlib.sha256(host).hexdigest()=='caece624998149737441172de399b6927b93b303e55fdd0123ae20904df1234b'
assert m.elf_metadata(host)['build_id']=='02f4a817c120c7589db38532c6891df016fcfbdc'
passed('actual_pinned_candidate_ELF_parses_as_static_data_only')
record={'schema':'frw.Root.GpgME-M1-repair-independent-delta-controls.v1','at_moscow':datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),
    'source_reviewer_result':ref(V/'RESULT.json'),'policy':ref(V/'repair-copy/gpgme_engine_policy.py'),'mapped':ref(V/'repair-copy/gpgme_mapped_image.py'),
    'checks':checks,'count':len(checks),'state':'PASS_SOURCE_PREPARATION_ONLY','actual_M':None,'new_live_operation':False,
    'limits':'Synthetic facts/identities/pipe/ELF and static host ELF only; no actual process/map/binding/argv/closure/Office/GPG qualification or permission. Original74 and reviewer evidence not rewritten.'}
path=Q/'ROOT-GPGME-M1-REPAIR-DELTA-CONTROLS.json';fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
with os.fdopen(fd,'w') as f:json.dump(record,f,ensure_ascii=False,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'result':ref(path),'count':len(checks),'state':record['state']}))
