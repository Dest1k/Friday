"""Two operator-admitted finite fixtures; no command/profile authority in args."""
from __future__ import annotations
import base64
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import stat
import threading

from .admission import CALL_FIELDS
from .artifacts import StagedArtifact, read_staged
from .associations import AssociationError
from .host_record import digest
from .results import output_root

FIXTURES = {
    'coding_add': ('host-repair', ['check.py', 'input/calculator.py', 'owner/test_calculator.py'], ['candidate']),
    'engineering_report': ('engineering-repair', ['check.py', 'input/report.py', 'input/readings.csv', 'owner/test_report.py'], ['settings', 'report']),
}
MAX_RAW = 32768


def strict_json(raw):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError('duplicate_check_json')
            result[k] = v
        return result
    def finite(s):
        value = float(s)
        if not math.isfinite(value):
            raise ValueError('nonfinite_check_json')
        return value
    def bad(s):
        raise ValueError('nonfinite_check_json')
    if not isinstance(raw, str) or len(raw.encode()) > MAX_RAW:
        raise ValueError('check_output_bound')
    result = json.loads(raw, object_pairs_hook=pairs, parse_float=finite, parse_constant=bad)
    if not isinstance(result, dict):
        raise ValueError('check_object_required')
    return result


def revision(row):
    return digest({'owner': row['owner'], 'binding': row['host']['binding'],
                   'artifacts': row['result']['artifacts'], 'paths': row['result']['source_paths']})


def files(row):
    return [{'reference': a['reference'], 'sha256': a['sha256'], 'size_bytes': a['size_bytes']}
            for a in row['result']['artifacts']]


def stable_source(path):
    # All components are checked, not merely a resolved leaf.
    p = Path(path)
    if not p.is_absolute() or '..' in p.parts:
        raise ValueError('check_source_path')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in p.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = child
        leaf = os.open(p.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            before = os.fstat(leaf)
            if (not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid()
                    or before.st_nlink != 1 or before.st_size > 65536):
                raise ValueError('check_source_type')
            data = os.read(leaf, 65537)
            after = os.fstat(leaf)
            named = os.stat(p.name, dir_fd=fd, follow_symlinks=False)
            def key(s):
                return s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_nlink,s.st_uid
            if key(before) != key(after) or key(after) != key(named) or len(data) != before.st_size:
                raise ValueError('check_source_drift')
            return data
        finally:
            os.close(leaf)
    finally:
        os.close(fd)


def admitted(host, row):
    from tools.terminal_scope import get_terminal_scope, TerminalPolicyRefusal
    from hermes_cli.lifecycle import has_hook
    if host.ctx.get_config('results') != {'enabled':True}:
        raise AssociationError('results_not_admitted')
    config = host.ctx.get_config('fixture_check')
    required = {'enabled', 'fixture', 'reference', 'owner_sha256', 'task_sha256',
                'artifacts', 'pins', 'terminal_scope_sha256', 'shell_init_reviewed', 'source_root'}
    if (not isinstance(config, dict) or set(config) != required or config['enabled'] is not True
            or config['fixture'] not in FIXTURES or config['shell_init_reviewed'] is not True
            or config['reference'] != row['existing_task_id']
            or config['owner_sha256'] != digest(row['owner'])
            or config['task_sha256'] != digest(row['host']['binding'])
            or config['artifacts'] != row['result']['artifacts']):
        raise AssociationError('fixture_not_admitted')
    from hermes_constants import get_hermes_home
    from hermes_yaml import safe_load
    actual=safe_load((get_hermes_home()/'config.yaml').read_text())
    terminal_config=actual.get('terminal',{})
    if terminal_config.get('shell_init_files') != [] or terminal_config.get('auto_source_bashrc') is not False:
        raise AssociationError('fixture_shell_init_not_admitted')
    scope = get_terminal_scope()
    if (not isinstance(scope, dict) or isinstance(scope, TerminalPolicyRefusal)
            or scope.get('TERMINAL_ENV') != 'local' or digest(scope) != config['terminal_scope_sha256']
            or has_hook('transform_terminal_output') or has_hook('transform_tool_result')):
        raise AssociationError('fixture_terminal_not_admitted')
    folder, paths, roles = FIXTURES[config['fixture']]
    expected = [f'fixtures/{folder}/{p}' for p in paths]
    if (not isinstance(config['pins'], dict) or set(config['pins']) != set(expected)
            or len(row['result']['artifacts']) != len(roles)):
        raise AssociationError('fixture_pins_invalid')
    source_root=Path(config['source_root'])
    if not source_root.is_absolute() or str(source_root)!=config['source_root'] or '..' in source_root.parts:
        raise AssociationError('fixture_source_root')
    for rel, sha in config['pins'].items():
        if not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{64}', sha) or hashlib.sha256(stable_source(source_root / rel)).hexdigest() != sha:
            raise AssociationError('fixture_source_changed')
    if (host._closed or row['stop_intent'] is not None or row['host']['quiescence'] is None
            or row['host']['terminal'] is None or row['host']['terminal']['state'] != 'completed'):
        raise AssociationError('fixture_stopped_or_unfinished')
    return copy.deepcopy(config)


def validate_observation(row, observed):
    required = {'call','kind','files','at_unix','revision','admission_sha256','fixture','state','native'}
    if (set(observed) != required or observed['kind'] != 'fixture_execution'
            or observed['fixture'] not in FIXTURES or observed['state'] not in {'UNKNOWN','PASS','FAIL'}
            or observed['revision'] != revision(row) or observed['files'] != files(row)
            or not isinstance(observed['admission_sha256'], str)
            or not re.fullmatch('[0-9a-f]{64}', observed['admission_sha256'])):
        raise AssociationError('invalid_fixture_observation')
    native = observed['native']
    if native is None:
        if observed['state'] != 'UNKNOWN':
            raise AssociationError('missing_fixture_native')
    elif (not isinstance(native, dict) or set(native) != {'raw', 'sha256'}
          or not isinstance(native['raw'], str) or len(native['raw'].encode()) > MAX_RAW
          or native['sha256'] != hashlib.sha256(native['raw'].encode()).hexdigest()):
        raise AssociationError('invalid_fixture_native')
    elif verdict(native['raw'], observed['fixture'], observed['files']) != observed['state']:
        raise AssociationError('fixture_verdict_mismatch')


def verdict(raw, fixture, artifacts):
    """A native exit and actual unchanged owner-test output, never accepted=true."""
    try:
        terminal = strict_json(raw)
        if (set(terminal) - {'output','exit_code','error','verification_evidence','exit_code_meaning','hint'}
                or terminal.get('error') is not None or type(terminal.get('exit_code')) is not int
                or terminal['exit_code'] not in (0,1)):
            return 'UNKNOWN'
        output=terminal['output']
        try:
            observation = strict_json(output)
        except ValueError:
            # Hermes may render canonical JSON string-body escaping. Decode
            # exactly one reversible layer; retain native raw. Never remove
            # redaction, ANSI, truncation or other text markers.
            decoded=json.loads('"'+output+'"')
            if json.dumps(decoded,ensure_ascii=True)[1:-1] != output:
                return 'UNKNOWN'
            observation = strict_json(decoded)
        common = {'accepted','returncode','executed','child_returncode','status','elapsed_seconds',
                  'artifact_sha256','owner_sha256','stdout','stderr','stdout_base64','stderr_base64','cleanup_completed'}
        if set(observation) != common or observation['status'] != 'completed' or observation['executed'] is not True or observation['cleanup_completed'] is not True:
            return 'UNKNOWN'
        for channel in ['stdout','stderr']:
            decoded = base64.b64decode(observation[channel+'_base64'], validate=True)
            if len(decoded)>16384 or decoded.decode('utf-8') != observation[channel]:
                return 'UNKNOWN'
        if type(observation['returncode']) is not int or observation['returncode'] not in (0,1) or observation['child_returncode'] != observation['returncode']:
            return 'UNKNOWN'
        if not isinstance(observation['elapsed_seconds'], (int,float)) or type(observation['elapsed_seconds']) is bool or not 0<=observation['elapsed_seconds']<=7:
            return 'UNKNOWN'
        count = 1 if fixture=='coding_add' else 5
        golden = ('3046b45b0b2c2702ac686ef1e946a6601c67d456a4e49b895566310674b33995'
                  if count==1 else 'b5ba3fde01b614ff95651a9f3f8306edbaa339764b4b7594e2ad39e6bec5460a')
        expected = artifacts[0]['sha256'] if count==1 else [a['sha256'] for a in artifacts]
        if observation['owner_sha256'] != golden or observation['artifact_sha256'] != expected:
            return 'UNKNOWN'
        stderr = observation['stderr']
        if not re.search(r'\nRan '+str(count)+r' tests? in [0-9.]+s\n', stderr):
            return 'UNKNOWN'
        if count==1 and 'test_add (test_calculator.CalculatorTest.test_add)' not in stderr:
            return 'UNKNOWN'
        if count==5 and len(re.findall(r'^test_\w+ \(test_report\.',stderr,re.M))!=5:
            return 'UNKNOWN'
        if observation['returncode']==0 and terminal['exit_code']==0 and stderr.rstrip().endswith('\nOK'):
            return 'PASS'
        if observation['returncode']==1 and terminal['exit_code']==1 and re.search(r'FAILED \((failures|errors)=\d+(, (failures|errors)=\d+)?\)\s*$',stderr):
            return 'FAIL'
    except (ValueError,KeyError,TypeError,UnicodeError,RecursionError):
        pass
    return 'UNKNOWN'


class FixtureChecks:
    def __init__(self, tool):
        self.tool=tool; self.host=tool.host; self.pending={}; self.lock=threading.Lock()

    def check(self, args, kwargs):
        from .result_tool import owned_result
        host=self.host
        if set(args)!= {'action','reference'}:
            raise AssociationError('fixture_arguments_refused')
        row=owned_result(host,args['reference'],kwargs)
        config=admitted(host,row)
        from .admission import _call
        call=dict(zip(CALL_FIELDS,_call.get())); ref=digest(call)
        observation={'call':call,'kind':'fixture_execution','files':files(row),'at_unix':host.store.clock(),
                     'revision':revision(row),'admission_sha256':digest(config),'fixture':config['fixture'],
                     'state':'UNKNOWN','native':None}
        with host.store._locked() as data:
            current=host.store._owned(data,row['existing_task_id'],row['owner'])
            if (revision(current)!=revision(row) or current['stop_intent'] is not None
                    or any(o['kind']=='fixture_execution' for o in current['result']['observations'].values())
                    or current['result']['assessment'] is not None or any(current['result']['deliveries'].values())
                    or len(current['result']['observations'])>=64):
                raise AssociationError('fixture_already_reserved_or_changed')
            current['result']['observations'][ref]=observation
            host.store._save(data)  # Crash/hook loss/reload never authorizes a replay.
        root=output_root(row).parent/'checks';root.mkdir(mode=0o700,exist_ok=True)
        from .host_runtime import private_directory
        private_directory(root)
        snap=root/ref;snap.mkdir(mode=0o700)
        folder, paths, roles=FIXTURES[config['fixture']]
        values={rel:stable_source(Path(config['source_root'])/rel) for rel in config['pins']}
        for rel,payload in values.items():
            if hashlib.sha256(payload).hexdigest()!=config['pins'][rel]:raise AssociationError('fixture_copy_source_drift')
        for artifact,role in zip(row['result']['artifacts'],roles):
            values['artifacts/'+role]=read_staged(staging_root=output_root(row),artifact=StagedArtifact(**artifact),max_bytes=65536)
        for rel, payload in values.items():
            p=snap/rel;p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400)
            with os.fdopen(fd,'wb') as stream:stream.write(payload);stream.flush();os.fsync(stream.fileno())
        checker=snap/f'fixtures/{folder}/check.py'
        argv=['/usr/bin/python3','-I','-S','-B',str(checker)]
        if config['fixture']=='coding_add':argv += [str(snap/'artifacts/candidate')]
        else:argv += ['--json-observation','--settings',str(snap/'artifacts/settings'),'--report',str(snap/'artifacts/report')]
        current=owned_result(host,args['reference'],kwargs)
        if admitted(host,current)!=config or revision(current)!=revision(row):raise AssociationError('fixture_before_dispatch_drift')
        raw=host.ctx.dispatch_tool('terminal',{'command':shlex.join(argv),'timeout':10,'background':False,'workdir':str(snap)},
                                   task_id=call['task_id'],session_id=call['session_id'])
        # No nested hook exists. Retain a one-use in-memory match for the REAL outer hook.
        current=owned_result(host,args['reference'],kwargs)
        if admitted(host,current)!=config or revision(current)!=revision(row):raise AssociationError('fixture_after_dispatch_drift')
        for artifact in row['result']['artifacts']:
            read_staged(staging_root=output_root(row),artifact=StagedArtifact(**artifact),max_bytes=65536)
        state=verdict(raw,config['fixture'],files(row))
        if not isinstance(raw,str) or len(raw.encode())>MAX_RAW:raw=None;state='UNKNOWN'
        response=json.dumps({'accepted':True,'reference':row['existing_task_id'],'observation_reference':ref,
                             'check_state':'PENDING_OUTER_HOOK','observed_candidate_state':state,'native':raw},sort_keys=True)
        with self.lock:
            if len(self.pending)>=64:return response
            self.pending[ref]={'row':row,'config':config,'args':copy.deepcopy(args),'call':call,
                               'response':response,'raw':raw,'state':state}
        return response

    def post_tool_call(self, *,tool_name=None,args=None,result=None,status=None,**kwargs):
        if tool_name!='friday_result' or not isinstance(args,dict) or args.get('action')!='check':return
        call={k:kwargs.get(k) for k in CALL_FIELDS};ref=digest(call)
        with self.lock:
            pending=self.pending.get(ref)
            if not pending or call!=pending['call'] or args!=pending['args'] or result!=pending['response'] or status!='ok':return
            self.pending.pop(ref)  # Single use even when the best-effort persistence fails.
        try:
            from .result_tool import current_result_owner
            row=current_result_owner(self.host,args['reference'],call['session_id'])
            config=admitted(self.host,row)
            if config!=pending['config'] or revision(row)!=revision(pending['row']):return
            for artifact in row['result']['artifacts']:
                read_staged(staging_root=output_root(row),artifact=StagedArtifact(**artifact),max_bytes=65536)
            with self.host.store._locked() as data:
                current=self.host.store._owned(data,row['existing_task_id'],row['owner'])
                observed=current['result']['observations'].get(ref)
                if (not observed or observed['state']!='UNKNOWN' or observed['native'] is not None
                        or current['stop_intent'] is not None or self.host._closed
                        or revision(current)!=revision(row)):return
                raw=pending['raw']
                observed['native']=None if raw is None else {'raw':raw,'sha256':hashlib.sha256(raw.encode()).hexdigest()}
                observed['state']=pending['state']
                self.host.store._save(data)
        except (ValueError,RuntimeError,OSError,TypeError,KeyError):
            return  # Durable reservation stays UNKNOWN; never replay.
