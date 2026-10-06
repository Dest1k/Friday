#!/usr/bin/env python3
"""Finite owned native Harness cases; systemd cgroup + bubblewrap, not an adapter."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('renderer', ROOT/'tools/render_dsh_local.py')
RENDERER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RENDERER)
PIN_CLI = '1a03dee18683483ff6a1b27b2a1e650230da6bcca9a0f55f7d81b3308c3f307f'
PIN_NODE = '3517c2df0b2f8cd7f422b4b8450ef81c6889f08eb03e281d6de9079b15e6a327'
LOCAL = 'http://192.168.1.78:8001'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(p, data):
    fd = os.open(p, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(data if isinstance(data, bytes) else (json.dumps(data, indent=2)+'\n').encode())

def private(p):
    p = p.absolute()
    p.mkdir(mode=0o700, parents=True, exist_ok=False)
    if p.resolve() != p or p.stat().st_uid != os.getuid() or p.stat().st_mode & 0o077:
        raise RuntimeError('Private owned directory required')
    return p

def show(unit):
    props = ['Id','LoadState','ActiveState','SubState','MainPID','ControlGroup','InvocationID','Result',
             'ExecMainCode','ExecMainStatus','RuntimeMaxUSec','KillMode','TimeoutStopUSec',
             'SendSIGKILL','TasksMax','MemoryMax','CPUQuotaPerSecUSec','NoNewPrivileges']
    r = subprocess.run(['systemctl','--user','show',unit,*['-p'+p for p in props]],
                       capture_output=True, timeout=5)
    values = dict(line.split('=',1) for line in r.stdout.decode().splitlines() if '=' in line)
    values['show_returncode'] = r.returncode
    cg = values.get('ControlGroup')
    values['cgroup_pids'] = []
    if cg:
        base = Path('/sys/fs/cgroup')/cg.lstrip('/')
        for p in base.rglob('cgroup.procs'):
            try:
                values['cgroup_pids'] += [int(x) for x in p.read_text().split()]
            except FileNotFoundError:
                pass
    return values

def metric_check(secret):
    request = urllib.request.Request(LOCAL+'/metrics', headers={'Authorization':'Bearer '+secret})
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=5) as r:
        body = r.read(2_000_000).decode()
    selected = [l for l in body.splitlines() if not l.startswith('#') and
                ('num_running_reqs' in l or 'num_queue_reqs' in l)]
    if not selected or not any('num_running_reqs' in l for l in selected) or not any('num_queue_reqs' in l for l in selected):
        raise RuntimeError('Load observation missing')
    idle = all(float(l.rsplit(' ',1)[-1]) == 0 for l in selected)
    return {'at':dt.datetime.now(dt.timezone.utc).isoformat(), 'lines':selected, 'idle':idle}

def key_value():
    # Read exactly the authorized local reference. Never persist or print it.
    text = Path('/home/jericho/.jericho/.env.local').read_text()
    matches = re.findall(r'^(?:export\s+)?FRIDAY_LLM_API_KEY\s*=\s*(.*)$', text, re.M)
    if len(matches) != 1:
        raise RuntimeError('Authorized key reference absent or ambiguous')
    value = matches[0].strip()
    if len(value)>1 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    if not value or '\n' in value or '\r' in value:
        raise RuntimeError('Invalid authorized key reference')
    return value

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', required=True, choices=['boundary','main','child','compact','inspect','reopen','disconnect','stop'])
    parser.add_argument('--node', type=Path, required=True)
    parser.add_argument('--donor', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--deadline', required=True)
    parser.add_argument('--seconds', type=int, required=True)
    parser.add_argument('--brief', type=Path)
    parser.add_argument('--session-id')
    parser.add_argument('--existing-home', type=Path)
    parser.add_argument('--existing-fixture', type=Path)
    args = parser.parse_args()
    if not __debug__:
        raise RuntimeError('Assertions required')
    deadline = dt.datetime.fromisoformat(args.deadline)
    remaining = (deadline-dt.datetime.now(dt.timezone.utc)).total_seconds()
    if args.seconds < 1 or args.seconds + 10 > remaining or args.seconds > 300:
        raise RuntimeError('Original deadline insufficient for case and cleanup')
    runtime, evidence = private(args.runtime), private(args.evidence)
    node, donor = args.node.resolve(strict=True), args.donor.resolve(strict=True)
    cli = donor/'apps/cli/lib/bin.js'
    assert sha(node) == PIN_NODE and sha(cli) == PIN_CLI, 'Accepted executable identity changed'
    fixture = args.existing_fixture.resolve(strict=True) if args.existing_fixture else private(runtime/'fixture')
    home = args.existing_home.resolve(strict=True) if args.existing_home else private(runtime/'home')
    for p in [fixture, home]:
        assert p.is_dir() and p.stat().st_uid==os.getuid() and not p.stat().st_mode & 0o077
        assert p.is_relative_to(ROOT/'.runtime/frw005-live'), 'Case directory outside assignment'
    inputs = private(runtime/'inputs')
    save(inputs/'case-id.txt',runtime.name.encode())
    profile = inputs/'local.patch.yml'
    patch = RENDERER.build_patch(purpose='temporary-local-test',api='openai-completions',
        base_url=LOCAL+'/v1',model='dispatcher',context_window=40960,max_tokens=4096,
        summary_max_tokens=2048,headroom_tokens=4096,api_key_env='FRIDAY_LLM_API_KEY',request_timeout_ms=60000)
    if args.case == 'disconnect':
        # Explicit harmless negative case, no credential or model request to a public route.
        patch[0]['config']['providers']['friday-local']['baseURL']='http://127.0.0.1:1/v1'
        patch[0]['config']['providers']['friday-local']['timeoutMs']=1000
    RENDERER.publish_private(profile,patch)
    save(inputs/'readonly-canary', b'owned readonly negative control\n')
    bootstrap = '''import os,sys
env={"PATH":sys.argv[1]+":/usr/bin:/bin","HOME":"/job-home","DSH_HOME":"/job-home/dsh","LANG":"C.UTF-8","DSH_TELEMETRY_DISABLED":"1","DSH_PERMISSION_MODE":"workspace-write"}
if "FRIDAY_LLM_API_KEY" in os.environ:env["FRIDAY_LLM_API_KEY"]=os.environ["FRIDAY_LLM_API_KEY"]
os.execve(sys.argv[2],sys.argv[2:],env)
'''
    save(inputs/'bootstrap.py', bootstrap.encode())
    host_bootstrap='''import os,sys
env={"PATH":"/usr/bin:/bin"}
if "FRIDAY_LLM_API_KEY" in os.environ:env["FRIDAY_LLM_API_KEY"]=os.environ["FRIDAY_LLM_API_KEY"]
os.execve(sys.argv[1],sys.argv[1:],env)
'''
    save(inputs/'host-bootstrap.py',host_bootstrap.encode())
    trace = ROOT/'scripts/dsh_live_trace.cjs'
    save(inputs/'trace.cjs',trace.read_bytes())
    save(inputs/'components.mjs',(ROOT/'scripts/dsh_live_components.mjs').read_bytes())
    save(inputs/'supervisor.py',Path(__file__).read_bytes())
    save(inputs/'held.patch.yml',[{'id':'headless-startup','disabled':True},{'id':'headless-runner','disabled':True}])
    bwrap = ['/usr/bin/bwrap','--unshare-user','--unshare-pid','--unshare-ipc','--unshare-uts',
        '--die-with-parent','--new-session','--cap-drop','ALL',
        '--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib',
        '--symlink','usr/lib64','/lib64','--proc','/proc','--dev','/dev','--size','67108864','--tmpfs','/tmp',
        '--ro-bind',str(node.parents[1]),str(node.parents[1]),'--ro-bind',str(donor),str(donor),
        '--ro-bind',str(inputs),'/job-input','--bind',str(fixture),'/workspace','--bind',str(home),'/job-home',
        '--ro-bind',str(inputs/'trace.cjs'),'/job-trace.cjs',
        '--ro-bind',str(inputs/'components.mjs'),'/job-components.mjs',
        '--chdir','/workspace','--remount-ro','/',
        '--','/usr/bin/python3','-I','/job-input/bootstrap.py',str(node.parent)]
    if args.case == 'boundary':
        control = '''import os,json,time,subprocess
checks={"host_home_hidden":not os.path.exists("/home/jericho/.jericho/.env.local"),"host_codex_hidden":not os.path.exists("/home/jericho/.codex"),"host_runtime_hidden":not os.path.exists("/run/user"),"root_readonly":False,"readonly_denied":False}
for p,k in [("/escape","root_readonly"),("/job-input/readonly-canary","readonly_denied")]:
 try:open(p,"w").write("denied")
 except OSError:checks[k]=True
open("/workspace/permitted","w").write("owned")
print(json.dumps(checks),flush=True)
assert all(checks.values())
pid=os.fork()
if pid==0:
 os.setsid()
 if os.fork():os._exit(0)
 while True:
  with open("/workspace/descendant-ticks","a") as f:f.write("tick\\n")
  time.sleep(.1)
while True:time.sleep(1)
'''
        command = bwrap+['/usr/bin/python3','-I','-c',control]
        brief, secret = b'', None
    else:
        component=args.case in ['child','compact','inspect']
        if args.brief is None and not component:
            raise RuntimeError('Explicit brief required')
        brief = args.brief.read_bytes() if args.brief else b''
        if len(brief)>50000:
            raise RuntimeError('Fixture brief excessive')
        if component:
            assert args.session_id and re.fullmatch(r'[A-Za-z0-9_.-]{1,128}',args.session_id)
            command=bwrap+[str(node),'--require','/job-trace.cjs','/job-components.mjs',str(donor),args.session_id,args.case]
        else:
            command = bwrap+[str(node),'--require','/job-trace.cjs',str(cli),'--profile','headless',
                             '--patch','/job-input/local.patch.yml','--json']
            if args.session_id:
                assert re.fullmatch(r'[A-Za-z0-9_.-]{1,128}',args.session_id)
                command += ['--session-id',args.session_id]
            command += ['-']
        secret = 'FRW005_NEGATIVE_LOCAL_CANARY' if args.case=='disconnect' else key_value()
    unit = 'frw005-live-'+args.case+'-'+runtime.name+'.service'
    assert re.fullmatch(r'[a-zA-Z0-9_.-]+',unit)
    env = {'PATH':'/usr/bin:/bin','XDG_RUNTIME_DIR':os.environ['XDG_RUNTIME_DIR']}
    if secret:
        env['FRIDAY_LLM_API_KEY']=secret
    launch = ['systemd-run','--user','--unit='+unit,'--pipe','--wait','--service-type=exec',
              '--expand-environment=no','--property=RuntimeMaxSec='+str(args.seconds)+'s',
              '--property=KillMode=control-group','--property=TimeoutStopSec=2s','--property=SendSIGKILL=yes',
              '--property=NoNewPrivileges=yes','--property=TasksMax=64','--property=MemoryMax=2G',
              '--property=CPUQuota=400%']
    if secret:
        launch += ['--setenv=FRIDAY_LLM_API_KEY']
    # Sanitise before the PID namespace exists, so its PID1 cannot expose manager credentials.
    launch += ['/usr/bin/python3','-I',str(inputs/'host-bootstrap.py'),*command]
    before = metric_check(key_value()) if args.case=='disconnect' else (metric_check(secret) if args.case!='boundary' else None)
    save(evidence/'launch.json',{'unit':unit,'argv':launch,'profile_sha256':sha(profile),
         'supervisor_sha256':sha(inputs/'supervisor.py'),'trace_sha256':sha(inputs/'trace.cjs'),
         'components_sha256':sha(inputs/'components.mjs'),
         'brief_sha256':hashlib.sha256(brief).hexdigest(),'deadline':args.deadline,
         'load_before':before,'node_sha256':sha(node),'cli_sha256':sha(cli),'case':args.case,
         'fixture':str(fixture),'home':str(home),'sequential_model_lane':True})
    if before and not before['idle']:
        save(evidence/'result.json',{'status':'DEFERRED_BUSY','load':before})
        print(json.dumps({'status':'DEFERRED_BUSY','evidence':str(evidence)}));return
    start=time.monotonic()
    child=subprocess.Popen(launch,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    launched_at=dt.datetime.now(dt.timezone.utc).isoformat()
    live=None
    try:
        try:
            stdout,stderr=child.communicate(brief,timeout=2 if args.case=='stop' else .5)
        except subprocess.TimeoutExpired:
            live=show(unit)
            save(evidence/'running-unit.json',live)
            if args.case=='stop':
                trace_path=home/'native-http.jsonl'
                save(evidence/'trace-at-stop.jsonl',trace_path.read_bytes() if trace_path.exists() else b'')
                subprocess.run(['systemctl','--user','stop',unit],check=True,timeout=5,capture_output=True)
            stdout,stderr=child.communicate(timeout=args.seconds+8)
    except BaseException:
        subprocess.run(['systemctl','--user','stop',unit],timeout=5,capture_output=True)
        try:stdout,stderr=child.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill();stdout,stderr=child.communicate(timeout=3)
        raise
    terminal=show(unit)
    # Inspect the recorded cgroup even if systemd has unloaded the unit.
    oldcg=(live or {}).get('ControlGroup')
    if oldcg:
        cg=Path('/sys/fs/cgroup')/oldcg.lstrip('/')
        pids=[]
        for p in cg.rglob('cgroup.procs'):
            try:pids += [int(x) for x in p.read_text().split()]
            except FileNotFoundError:pass
        terminal['recorded_cgroup_pids']=pids
        terminal['recorded_cgroup_exists']=cg.exists()
        assert not pids,'Owned descendants remain'
    assert terminal.get('MainPID','0')=='0' and not terminal.get('cgroup_pids'), 'Unit still running'
    leaked=False
    if secret:
        key=secret.encode()
        leaked=key in stdout+stderr
        stdout=stdout.replace(key,b'[REDACTED_LOCAL_KEY]');stderr=stderr.replace(key,b'[REDACTED_LOCAL_KEY]')
        for p in home.rglob('*'):
            if p.is_file() and not p.is_symlink():
                if key in p.read_bytes():leaked=True
    save(evidence/'stdout',stdout);save(evidence/'stderr',stderr)
    events=[]
    if args.case!='boundary':
        for line in stdout.splitlines():
            try:events.append(json.loads(line))
            except ValueError:pass
    result={'case':args.case,'launched_at':launched_at,'finished_at':dt.datetime.now(dt.timezone.utc).isoformat(),
       'elapsed_seconds':time.monotonic()-start,'process_exit':child.returncode,'unit':unit,
       'terminal_unit':terminal,'secret_leak_observed':leaked,
       'session_ids':[e['sessionId'] for e in events if e.get('type')=='session'],
       'turn_end_reasons':[e.get('reason') for e in events if e.get('type')=='status' and e.get('phase')=='turn_end'],
       'tool_calls':[e.get('tool',e.get('name',e.get('toolName'))) for e in events if e.get('type')=='tool_call'],
       'tool_result_count':sum(e.get('type')=='tool_result' for e in events),
       'final_present':any(e.get('type')=='final' for e in events),
       'stdout_sha256':hashlib.sha256(stdout).hexdigest(),'stderr_sha256':hashlib.sha256(stderr).hexdigest(),
       'fixture_files':{str(p.relative_to(fixture)):sha(p) for p in fixture.rglob('*') if p.is_file() and not p.is_symlink()},
       'live_completion':False,'goal_verified':False}
    result['live_completion']=child.returncode==0 and any(r and r.get('kind')=='completed' for r in result['turn_end_reasons']) and not leaked
    if args.case in ['child','compact','inspect']:
        component_path=home/('component-'+args.case+'-'+runtime.name+'.json')
        if component_path.exists():
            report_bytes=component_path.read_bytes()
            if secret and secret.encode() in report_bytes:
                raise RuntimeError('Secret in component report; stop this lane')
            save(evidence/'component-report.json',report_bytes)
            result['native_component_status']=json.loads(report_bytes)['status']
            result['component_report_sha256']=hashlib.sha256(report_bytes).hexdigest()
    save(evidence/'result.json',result)
    print(json.dumps({k:result[k] for k in ['case','process_exit','elapsed_seconds','session_ids','turn_end_reasons','tool_result_count','live_completion','secret_leak_observed']}))
    if leaked:raise RuntimeError('Secret appeared in native artifact; stop this lane')

if __name__=='__main__':
    main()
