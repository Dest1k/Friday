#!/usr/bin/env python3
"""One finite acceptance case using the existing user supervisor and outer OS boundary."""
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
STAGE = Path('/home/jericho/jericho/Friday_rework/.runtime/dsh-native-complete/frw005-g1-012jccbe/dsh')
NODE = Path('/home/jericho/.jericho/runtime/friday-toolchain22.bSt8Uu/node-v22.23.2-linux-x64/bin/node')
LOCAL = 'http://192.168.1.78:8001'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(p, data):
    with os.fdopen(os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as f:
        f.write(data if isinstance(data, bytes) else (json.dumps(data, indent=2) + '\n').encode())

def private(p):
    p.mkdir(mode=0o700)
    assert p.resolve() == p and p.stat().st_uid == os.getuid() and not p.stat().st_mode & 0o077
    return p

def show(unit):
    names = ['Id','LoadState','ActiveState','SubState','MainPID','ControlGroup','InvocationID','Result',
             'ExecMainCode','ExecMainStatus','RuntimeMaxUSec','KillMode','TimeoutStopUSec','SendSIGKILL',
             'TasksMax','MemoryMax','CPUQuotaPerSecUSec','NoNewPrivileges']
    r = subprocess.run(['systemctl','--user','show',unit,*['-p'+n for n in names]], capture_output=True, timeout=5)
    d = dict(l.split('=',1) for l in r.stdout.decode().splitlines() if '=' in l)
    d['show_returncode'] = r.returncode
    d['cgroup_pids'] = cgroup_pids(d.get('ControlGroup'))
    return d

def cgroup_pids(name):
    found = []
    if name:
        for p in (Path('/sys/fs/cgroup') / name.lstrip('/')).rglob('cgroup.procs'):
            try: found.extend(int(i) for i in p.read_text().split())
            except FileNotFoundError: pass
    return found

def secret_value():
    matches = re.findall(r'^(?:export\s+)?FRIDAY_LLM_API_KEY\s*=\s*(.*)$', Path('/home/jericho/.jericho/.env.local').read_text(), re.M)
    assert len(matches) == 1
    v = matches[0].strip()
    if len(v)>1 and v[0] == v[-1] and v[0] in "\"'": v = v[1:-1]
    assert v and '\n' not in v and '\r' not in v
    return v

def load(secret):
    req = urllib.request.Request(LOCAL+'/metrics', headers={'Authorization':'Bearer '+secret})
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=5) as r:
        text = r.read(2_000_000).decode()
    lines = [l for l in text.splitlines() if not l.startswith('#') and ('num_running_reqs' in l or 'num_queue_reqs' in l)]
    assert any('num_running_reqs' in l for l in lines) and any('num_queue_reqs' in l for l in lines)
    return {'at':dt.datetime.now(dt.timezone.utc).isoformat(),'lines':lines,'idle':all(float(l.rsplit(' ',1)[-1])==0 for l in lines)}

def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', required=True, choices=['enforcement','deadline','stop','coding'])
    args = parser.parse_args()
    received = json.loads(Path('/home/jericho/.jericho/runtime/sol-fresh-rebind-20261006-01a111ad/FRW005-NATIVE-FULL-received.json').read_bytes())
    seconds = {'enforcement':30,'deadline':4,'stop':60,'coding':300}[args.case]
    remaining = (dt.datetime.fromisoformat(received['deadline_msk'])-dt.datetime.now(dt.timezone.utc)).total_seconds()
    assert seconds + 15 < remaining
    for ref in received['verified_input_refs']:
        assert sha(ref['path']) == ref['sha256'], ref['path']
    assert sha(NODE)=='3517c2df0b2f8cd7f422b4b8450ef81c6889f08eb03e281d6de9079b15e6a327'
    cli = STAGE/'apps/cli/lib/bin.js'
    assert sha(cli)=='1a03dee18683483ff6a1b27b2a1e650230da6bcca9a0f55f7d81b3308c3f307f'
    runtime = private(ROOT/'.runtime/frw005-native-full'/args.case)
    evidence = private(ROOT/'.evidence/frw005-native-full'/args.case)
    fixture, home, inputs = [private(runtime/n) for n in ['fixture','home','inputs']]
    save(inputs/'readonly-canary', b'owned readonly negative control\n')
    for name, source in [('gate.mjs',ROOT/'scripts/dsh_native_full_gate.mjs'),('trace.cjs',ROOT/'scripts/dsh_native_full_trace.cjs'),('supervisor.py',Path(__file__))]:
        save(inputs/name,source.read_bytes())
    save(inputs/'host-bootstrap.py', b'import os,sys\nenv={"PATH":"/usr/bin:/bin"}\nif "FRIDAY_LLM_API_KEY" in os.environ:env["FRIDAY_LLM_API_KEY"]=os.environ["FRIDAY_LLM_API_KEY"]\nos.execve(sys.argv[1],sys.argv[1:],env)\n')
    save(inputs/'bootstrap.py', b'import os,sys\nenv={"PATH":sys.argv[1]+":/usr/bin:/bin","HOME":"/job-home","DSH_HOME":"/job-home/dsh","LANG":"C.UTF-8","DSH_TELEMETRY_DISABLED":"1","DSH_PERMISSION_MODE":"workspace-write"}\nif "FRIDAY_LLM_API_KEY" in os.environ:env["FRIDAY_LLM_API_KEY"]=os.environ["FRIDAY_LLM_API_KEY"]\nos.execve(sys.argv[2],sys.argv[2:],env)\n')
    secret, before, brief = None, None, b''
    if args.case == 'coding':
        spec = importlib.util.spec_from_file_location('render',ROOT/'tools/render_dsh_local.py')
        renderer = importlib.util.module_from_spec(spec);spec.loader.exec_module(renderer)
        renderer.publish_private(inputs/'local.patch.yml',renderer.build_patch(purpose='temporary-local-test',api='openai-completions',base_url=LOCAL+'/v1',model='dispatcher',context_window=40960,max_tokens=4096,summary_max_tokens=2048,headroom_tokens=4096,api_key_env='FRIDAY_LLM_API_KEY',request_timeout_ms=60000))
        save(fixture/'calculator.py',b'def add(a, b):\n    return a - b\n')
        save(fixture/'test_calculator.py',b'import unittest\nfrom calculator import add\nclass CalculatorTest(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(add(7, 5), 12)\n        self.assertEqual(add(-2, 3), 1)\n        self.assertEqual(add(0, 0), 0)\nif __name__ == "__main__": unittest.main()\n')
        baseline = subprocess.run(['/usr/bin/python3','-I','-c',"import sys,unittest;sys.path.insert(0,'.');import test_calculator;r=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromModule(test_calculator));sys.exit(not r.wasSuccessful())"],cwd=fixture,capture_output=True,timeout=5)
        save(evidence/'baseline.stdout',baseline.stdout);save(evidence/'baseline.stderr',baseline.stderr)
        assert baseline.returncode == 1 and b'AssertionError' in baseline.stderr
        brief = b'Fix the actual bug in calculator.py. Read both supplied files first, run the existing test with python3 -B -m unittest -v test_calculator.py to observe the failure, repair only calculator.py, then run that same test to prove success. Do not modify the test, install anything, use network tools, create children, or change permission policy. Stop after a passing test and report the change.\n'
        secret = secret_value(); before = load(secret)
        if not before['idle']:
            save(evidence/'result.json',{'status':'DEFERRED_BUSY','load':before});print('DEFERRED_BUSY');return
        command = [str(NODE),'--require','/job-input/trace.cjs',str(cli),'--profile','headless','--patch','/job-input/local.patch.yml','--json','-']
    else:
        command = [str(NODE),'/job-input/gate.mjs',str(STAGE),args.case]
    bwrap = ['/usr/bin/bwrap','--unshare-user','--unshare-pid','--unshare-ipc','--unshare-uts',
             '--die-with-parent','--new-session','--cap-drop','ALL','--ro-bind','/usr','/usr',
             '--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64',
             '--proc','/proc','--dev','/dev','--size','67108864','--tmpfs','/tmp',
             '--ro-bind',str(NODE.parents[1]),str(NODE.parents[1]),'--ro-bind',str(STAGE),str(STAGE),
             '--ro-bind',str(inputs),'/job-input','--bind',str(fixture),'/workspace','--bind',str(home),'/job-home',
             '--chdir','/workspace','--remount-ro','/','--','/usr/bin/python3','-I','/job-input/bootstrap.py',str(NODE.parent),*command]
    unit = 'frw005-native-full-'+args.case+'.service'
    env = {'PATH':'/usr/bin:/bin','XDG_RUNTIME_DIR':os.environ['XDG_RUNTIME_DIR']}
    launch = ['systemd-run','--user','--unit='+unit,'--pipe','--wait','--service-type=exec','--expand-environment=no',
              '--property=RuntimeMaxSec='+str(seconds)+'s','--property=KillMode=control-group','--property=TimeoutStopSec=2s',
              '--property=SendSIGKILL=yes','--property=NoNewPrivileges=yes','--property=TasksMax=64',
              '--property=MemoryMax=2G','--property=CPUQuota=400%']
    if secret:env['FRIDAY_LLM_API_KEY']=secret;launch+=['--setenv=FRIDAY_LLM_API_KEY']
    launch+=['/usr/bin/python3','-I',str(inputs/'host-bootstrap.py'),*bwrap]
    save(evidence/'launch.json',{'unit':unit,'argv':launch,'load_before':before,'seconds':seconds,'deadline':received['deadline_msk'],'inputs':{p.name:sha(p) for p in inputs.iterdir()},'fixture':str(fixture),'home':str(home),'brief_sha256':hashlib.sha256(brief).hexdigest()})
    start = time.monotonic();live = None
    child = subprocess.Popen(launch,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        try: stdout,stderr = child.communicate(brief,timeout=2 if args.case=='stop' else .5)
        except subprocess.TimeoutExpired:
            live = show(unit);save(evidence/'running-unit.json',live)
            if args.case=='stop':
                assert (fixture/'ready').read_text()=='NATIVE_FULL' and (fixture/'descendant-ticks').stat().st_size>0
                subprocess.run(['systemctl','--user','stop',unit],capture_output=True,timeout=5,check=True)
            stdout,stderr = child.communicate(timeout=seconds+8)
    except BaseException:
        subprocess.run(['systemctl','--user','stop',unit],capture_output=True,timeout=5)
        try:stdout,stderr=child.communicate(timeout=5)
        except subprocess.TimeoutExpired:child.kill();stdout,stderr=child.communicate(timeout=3)
        save(evidence/'aborted.stdout',stdout);save(evidence/'aborted.stderr',stderr)
        save(evidence/'aborted-unit.json',show(unit))
        raise
    terminal = show(unit)
    terminal['recorded_cgroup_pids'] = cgroup_pids((live or {}).get('ControlGroup'))
    assert terminal.get('MainPID','0')=='0' and not terminal['cgroup_pids'] and not terminal['recorded_cgroup_pids']
    leak = bool(secret and secret.encode() in stdout+stderr)
    if secret:
        key=secret.encode();stdout=stdout.replace(key,b'[REDACTED_LOCAL_KEY]');stderr=stderr.replace(key,b'[REDACTED_LOCAL_KEY]')
        leak |= any(key in p.read_bytes() for p in home.rglob('*') if p.is_file() and not p.is_symlink())
    save(evidence/'stdout',stdout);save(evidence/'stderr',stderr)
    events=[]
    for line in stdout.splitlines():
        try: events.append(json.loads(line))
        except ValueError: pass
    result={'case':args.case,'elapsed_seconds':time.monotonic()-start,'process_exit':child.returncode,'terminal_unit':terminal,'secret_leak_observed':leak,'session_ids':[e['sessionId'] for e in events if e.get('type')=='session'],'turn_end_reasons':[e.get('reason') for e in events if e.get('type')=='status' and e.get('phase')=='turn_end'],'tool_result_count':sum(e.get('type')=='tool_result' for e in events),'final_present':any(e.get('type')=='final' for e in events),'fixture_files':{str(p.relative_to(fixture)):sha(p) for p in fixture.rglob('*') if p.is_file() and not p.is_symlink()},'native_reports':[e for e in events if e.get('kind')==args.case]}
    if args.case in ['deadline','stop']:
        ticks=fixture/'descendant-ticks';after=ticks.read_bytes();time.sleep(.3)
        result['descendant_ticks_stable']=after==ticks.read_bytes();result['native_ready']=(fixture/'ready').read_text()=='NATIVE_FULL'
        assert result['descendant_ticks_stable'] and result['native_ready']
    if args.case=='coding':
        check=subprocess.run(['/usr/bin/python3','-B','-m','unittest','-v','test_calculator.py'],cwd=fixture,capture_output=True,timeout=5)
        save(evidence/'after-test.stdout',check.stdout);save(evidence/'after-test.stderr',check.stderr)
        result['actual_test_exit']=check.returncode
        result['test_unchanged']=sha(fixture/'test_calculator.py')==hashlib.sha256(b'import unittest\nfrom calculator import add\nclass CalculatorTest(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(add(7, 5), 12)\n        self.assertEqual(add(-2, 3), 1)\n        self.assertEqual(add(0, 0), 0)\nif __name__ == "__main__": unittest.main()\n').hexdigest()
        result['coding_goal_verified']=child.returncode==0 and any(r and r.get('kind')=='completed' for r in result['turn_end_reasons']) and result['tool_result_count']>0 and check.returncode==0 and result['test_unchanged'] and not leak
    save(evidence/'result.json',result);print(json.dumps(result))
    assert not leak
    if args.case=='enforcement':assert child.returncode==0 and any(e.get('status')=='PASS_FULL_AUTOMATIC_ENFORCEMENT' for e in events)
    if args.case=='deadline':assert terminal.get('Result')=='timeout'
    if args.case=='coding':assert result['coding_goal_verified']

if __name__=='__main__':main()
