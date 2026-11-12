import datetime,json,os,resource,runpy,signal,sys,time
from pathlib import Path
os.umask(0o077);sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent;W=B/'checks'
kind=sys.argv[1];recipe=json.loads((W/'COMMANDS.json').read_bytes());argv=recipe['commands'][kind]
available=sorted(os.sched_getaffinity(0));os.sched_setaffinity(0,available[:2])
resource.setrlimit(resource.RLIMIT_CPU,(600,600));resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
started=time.monotonic()
def now():return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat()
def expired(*unused):raise TimeoutError('core208_source_check_wall_budget_exhausted')
signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,900)
for variable,suffix in [('HERMES_HOME','hermes-home'),('TMPDIR','tmp'),('XDG_CACHE_HOME','cache')]:
 p=W/'sandbox'/kind/suffix;p.mkdir(parents=True,mode=0o700,exist_ok=True);os.environ[variable]=str(p)
os.environ['FRW_F06_DEADLINE_MONOTONIC']=str(started+900);os.environ['PATH']='/usr/bin:/bin';os.environ['GIT_OPTIONAL_LOCKS']='0'
record=dict(state='RUNNING_SOURCE_ONLY',kind=kind,started=now(),argv=argv,pid=os.getpid(),affinity=sorted(os.sched_getaffinity(0)),original_available_cpus=available,limits=recipe['limits'])
record['resource_before']={p:Path('/sys/fs/cgroup',p).read_text().strip() for p in ['cpu.max','memory.max','memory.current','cpu.pressure','io.pressure'] if Path('/sys/fs/cgroup',p).exists()}
out=W/(kind+'.json');out.write_text(json.dumps(record,indent=2)+'\n');out.chmod(0o600)
try:
 sys.argv=argv;runpy.run_path(argv[0],run_name='__main__');record['state']='COMPLETED_SOURCE_ONLY_SEE_REPORT'
except BaseException as exc:
 record['state']='FAILED_SOURCE_CHECK';record['exception_class']=type(exc).__name__;raise
finally:
 signal.setitimer(signal.ITIMER_REAL,0);u=resource.getrusage(resource.RUSAGE_SELF);c=resource.getrusage(resource.RUSAGE_CHILDREN)
 record.update(completed=now(),wall_seconds=time.monotonic()-started,combined_cpu_seconds=u.ru_utime+u.ru_stime+c.ru_utime+c.ru_stime,maxrss_kib=u.ru_maxrss)
 out.write_text(json.dumps(record,indent=2)+'\n')
