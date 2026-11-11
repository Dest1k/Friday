"""Pure/isolated NONSECRET observer checks; never invoke native qualification."""
from pathlib import Path
import ast, hashlib, json, os, shutil, subprocess, sys, types

ROOT = Path(__file__).resolve().parent
OLD = Path('/home/jericho/.cache/FRW-SOL-V3-F06-PROTECTED-OFFICE-CORE-20261111/native-harness/revision3/harness.py')
NEW = ROOT / 'candidate/harness.py'
TESTROOT = ROOT / 'tests'
os.umask(0o077)
TESTROOT.mkdir(mode=0o700, exist_ok=True)


def load(path):
    namespace = {'__name__': 'source_only_observer_test', '__file__': str(path)}
    exec(compile(path.read_text(), str(path), 'exec'), namespace)
    return namespace


def capture(path, tag):
    ns = load(path)
    case = TESTROOT / tag
    case.mkdir(mode=0o700)
    base, source = case / 'base', case / 'native-source'
    base.mkdir(mode=0o700); source.mkdir(mode=0o700)
    work = base / 'work'; work.mkdir(mode=0o700)
    pins = {'files': [{'relative': 'pinned.py'}], 'resources': []}
    (base / 'SOURCE-PINS.json').write_text(json.dumps(pins))
    hook = []
    fake_os = types.SimpleNamespace(**{key: getattr(os, key) for key in dir(os)})
    fake_os.environ = {}
    fake_os.chdir = lambda *_: None
    fake_os.umask = lambda *_: None
    fake_sys = types.SimpleNamespace(prefix=sys.prefix, base_prefix=sys.base_prefix,
        addaudithook=hook.append, path=[], _getframe=sys._getframe)
    fake_resource = types.SimpleNamespace(setrlimit=lambda *_: None,
        RLIMIT_CPU=1, RLIMIT_AS=2, RLIMIT_FSIZE=3, RLIMIT_NOFILE=4)
    ns.update(BASE=base, PARENT=case, SOURCE=source, sys=fake_sys, os=fake_os,
        resource=fake_resource, DENIED=[])
    manifest = {'credential': {'path': str(case / 'outside' / 'NONSECRET-CREDENTIAL')},
        'fixtures': [{'input': {'path': str(case / 'outside' / 'NONSECRET-INPUT')}}]}
    ns['install_boundary'](work, manifest)
    return ns, hook[0], case, base, work, source, manifest


def cases(case, base, work, source, manifest):
    outside = case / 'outside' / 'NONSECRET-PATH-SENTINEL'
    return [
      ('own_read', 'open', (str(work/'toy'), None, os.O_RDONLY)),
      ('own_write', 'open', (str(work/'toy'), None, os.O_WRONLY|os.O_CREAT)),
      ('fd_read', 'open', (27, None, os.O_RDONLY)),
      ('fd_write', 'open', (27, None, os.O_WRONLY)),
      ('pinned_source_read', 'open', (str(source/'pinned.py'), None, os.O_RDONLY)),
      ('unpinned_source_read', 'open', (str(source/'NONSECRET-UNPINNED.py'), None, os.O_RDONLY)),
      ('source_write', 'open', (str(source/'pinned.py'), None, os.O_WRONLY)),
      ('outside_read', 'open', (str(outside), None, os.O_RDONLY)),
      ('outside_write', 'open', (str(outside), None, os.O_WRONLY|os.O_CREAT)),
      ('outside_directory_open_legacy', 'open', (str(outside.parent), None, os.O_RDONLY|os.O_DIRECTORY)),
      ('dependency_read', 'open', ('/usr/lib/NONSECRET.py', None, os.O_RDONLY)),
      ('exact_credential_toy', 'open', (manifest['credential']['path'], None, os.O_RDONLY)),
      ('source_directory_open_legacy', 'open', (str(source/'unknown'), None, os.O_DIRECTORY)),
      ('mkdir_own', 'os.mkdir', (str(work/'new'), 0o700, -1)),
      ('mkdir_outside', 'os.mkdir', (str(outside), 0o700, -1)),
      ('remove_outside', 'os.remove', (str(outside), -1)),
      ('rename_outside', 'os.rename', (str(work/'toy'), str(outside), -1, -1)),
      ('link_outside', 'os.link', (str(work/'toy'), str(outside), -1, -1)),
      ('sqlite_memory', 'sqlite3.connect', (':memory:',)),
      ('sqlite_own', 'sqlite3.connect', (str(work/'db'),)),
      ('sqlite_outside', 'sqlite3.connect', ('file:'+str(outside)+'?mode=ro',)),
      ('process_denial', 'subprocess.Popen', ('NONSECRET', [], None, {})),
      ('socket_denial', 'socket.connect', (None, ('NONSECRET', 1))),
      ('source_list', 'os.listdir', (str(source),)),
      ('parent_list', 'os.scandir', (str(case),)),
      ('outside_list', 'os.listdir', ('/NONSECRET-FORBIDDEN',)),
    ]


def result(ns, hook, event, args):
    try:
        hook(event, args)
        return 'allowed'
    except ns['Refused'] as error:
        assert str(error) == 'python_audit_boundary'
        return 'denied'


fixture_ns = load(NEW)
assert all(fixture_ns['audit_fixture_label'](value) == value for value in ('f06-1','f06-4','f06-5','f06-6','f06-7'))
assert all(fixture_ns['audit_fixture_label'](value) == 'unclassified_fixture' for value in (None, [], {}, 5, 'NONSECRET-INPUT-SENTINEL'))

old = capture(OLD, 'old-policy')
new = capture(NEW, 'new-policy')
old_cases = cases(*old[2:])
new_cases = cases(*new[2:])
checks = []
for before, after in zip(old_cases, new_cases):
    assert before[0:2] == after[0:2]
    a = result(old[0], old[1], before[1], before[2])
    b = result(new[0], new[1], after[1], after[2])
    assert a == b, before[0]
    checks.append({'control': before[0], 'decision': b, 'unchanged': True})
serialized = json.dumps(new[0]['DENIED'])
assert 'NONSECRET-PATH-SENTINEL' not in serialized
assert 'NONSECRET-UNPINNED' not in serialized
assert 'NONSECRET-CREDENTIAL' not in serialized
assert str(new[2]) not in serialized
assert all('boundary_rule' in row and row['fixture'] == 'none' for row in new[0]['DENIED'])
open_rows = [row for row in new[0]['DENIED'] if row['event'] == 'open']
assert all(type(row['open_flags']) is int and len(row['path_sha256']) == 64 for row in open_rows)
# A synthetic call compiled at pinned code gets a trusted source location, no locals.
fragment = compile("def source_call(hook, path):\n    secret_local = 'NONSECRET-LOCAL-SENTINEL'\n    hook('open', (path, None, 0))\n", str(new[5]/'pinned.py'), 'exec')
context = {}; exec(fragment, context)
try:
    context['source_call'](new[1], '/NONSECRET-STACK-PATH')
except new[0]['Refused']:
    pass
row = new[0]['DENIED'][-1]
assert {'kind':'pinned_native_source','relative':'pinned.py','line':3} in row['source_locations']
assert 'NONSECRET-LOCAL-SENTINEL' not in json.dumps(row)
# Observation failure is fail-closed and keeps the original fixed Refused code.
new[0]['sha'] = lambda _: (_ for _ in ()).throw(ValueError('NONSECRET-ERROR-SENTINEL'))
assert result(new[0],new[1],'open',('/NONSECRET-ERROR-PATH',None,0)) == 'denied'
assert new[0]['DENIED'][-1]['metadata_status'] == 'incomplete_fixed_no_exception_message'
assert 'NONSECRET-ERROR-SENTINEL' not in json.dumps(new[0]['DENIED'])
# No new dependencies, launch paths, pins or policy branches in the source diff.
a = ast.parse(OLD.read_text()); b = ast.parse(NEW.read_text())
imports = lambda tree: [ast.dump(x) for x in ast.walk(tree) if isinstance(x,(ast.Import,ast.ImportFrom))]
assert imports(a) == imports(b)
for name in ('source_read_allowed','binding_check','pins_check','main'):
    find=lambda tree:next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
    assert ast.dump(find(a)) == ast.dump(find(b)), name

# Register a real CPython audit hook in a disposable subprocess on toy paths.
# This exercises true 'open' event flags and refusal-before-I/O without native imports.
actual = r'''
from pathlib import Path
import json,os,sys
root=Path(sys.argv[1]); candidate=Path(sys.argv[2])
ns={'__name__':'isolated_observer_control','__file__':str(candidate)}
exec(compile(candidate.read_text(),str(candidate),'exec'),ns)
case=root/'real-audit';case.mkdir(mode=0o700)
base=case/'base';base.mkdir(mode=0o700)
source=case/'source';source.mkdir(mode=0o700)
(source/'pinned.py').write_text('NONSECRET-PINNED')
(source/'unbound.py').write_text('NONSECRET-UNBOUND')
(base/'SOURCE-PINS.json').write_text(json.dumps({'files':[{'relative':'pinned.py'}]}))
work=base/'work';work.mkdir(mode=0o700)
outside=case/'outside';outside.mkdir(mode=0o700)
(outside/'toy').write_text('NONSECRET-OUTSIDE')
ns.update(BASE=base,PARENT=case,SOURCE=source)
ns['install_boundary'](work,{'credential':{'path':str(outside/'exact-toy')},'fixtures':[]})
(work/'own').write_text('NONSECRET-OWN')
assert (work/'own').read_text()=='NONSECRET-OWN'
assert (source/'pinned.py').read_text()=='NONSECRET-PINNED'
for path in (source/'unbound.py',outside/'toy'):
    try:path.read_bytes()
    except ns['Refused']:pass
    else:raise AssertionError('expected denial')
try:(outside/'new').write_text('NONSECRET-BLOCKED')
except ns['Refused']:pass
else:raise AssertionError('expected denial')
assert not (outside/'new').exists()
assert len(ns['DENIED'])==3
assert all(type(row['open_flags']) is int for row in ns['DENIED'])
print(json.dumps({'true_audit_open_denials':len(ns['DENIED']),'denied_write_absent':True,'pinned_read_allowed':True,'own_write_read_allowed':True,'native_imports':False,'encrypted_operations':False}))
'''
proc = subprocess.run([sys.executable,'-B','-c',actual,str(TESTROOT),str(NEW)],
  text=True, capture_output=True, timeout=30)
assert proc.returncode == 0, {'exit':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr}
real = json.loads(proc.stdout)
report = {'schema':'friday.f06.metadata-observer-controls.v1','status':'PASS',
 'scope':'pure captured-policy equivalence plus real isolated CPython audit on NONSECRET toys only',
 'policy_controls':checks,'denial_count':len(new[0]['DENIED']),
 'no_raw_path_or_local_or_exception_message':True,'metadata_failure_still_refused':True,
 'trusted_pinned_source_location_retained':True,'subset_fixture_ids_truthful_and_fixed_whitelist':True,'existing_launch_binding_pins_functions_unchanged':True,
 'real_audit_controls':real,'native_or_encrypted_or_office_execution':False}
(ROOT/'TEST-RESULTS.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.rmtree(TESTROOT)
print(json.dumps({'status':report['status'],'policy_cases':len(checks),'real':real}))
