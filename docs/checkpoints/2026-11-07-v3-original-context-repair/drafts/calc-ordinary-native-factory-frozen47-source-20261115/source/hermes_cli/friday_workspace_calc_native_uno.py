"""Fixed ordinary inner entry SOURCE. Importing this module never imports UNO.

Only the owned PID1 supervisor executes ``main`` in the existing sole ordinary
namespace. The dynamic transport binds the current source/process; it is not a
proof/admission API. Managed source, launch, native/helper custody, final joins
and terminal observation are independently owned by the fixed factory.
"""
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import time

WORK = Path('/tmp/friday-metric-work')
CODE = WORK / 'code'
PROGRAM = Path('/opt/friday-document-toolchain/root/usr/lib/libreoffice/program')
CONFIG = WORK / 'ordinary-inner.json'
LIFECYCLE = 'DESKTOP_PREPARE_LOCALE_COMPLETED_NO_LATER_LANGUAGE_MUTATION'
SCHEMA = 'frw.ordinary-calc.inner-config.v1'
UNO_FILES = (
    ('uno/python/uno.py', 'c3020eb13e43c0a3b33a73b0c1234017f556186ced5ee88d0d1483b3ad0cae4f'),
    ('uno/python/unohelper.py', '0aa4d49ca34e12f1facef61990f98a1817f419c6125d156cca8d968f1c88b389'),
    ('uno/program/pyuno.so', 'aa7eb3185fbd7e82dd95d3a5352f8a012824e674819562ebfe867bc5a59c648c'),
    ('uno/program/libpyuno.so', '9447d12c57f1cbca739791a227a47a7128b561225805741c6ce8029dafec362d'),
)
_CONFIG_FIELDS = {'schema','nonce','source_sha256','source_bytes','pipe_name',
                  'process','symbols','started_monotonic','parent_deadline','deadline'}
_DESCRIPTOR_TYPES = {
    'Name': str, 'Height': int, 'Width': int, 'StyleName': str, 'Family': int,
    'CharSet': int, 'Pitch': int, 'CharacterWidth': float, 'Weight': float,
    'Slant': str, 'Underline': int, 'Strikeout': int, 'Orientation': float,
    'Kerning': bool, 'WordLineMode': bool, 'Type': int,
}


class UnoConstructionRefused(ValueError):
    """Stable code only; no exception/config/user text enters returned records."""


def need(condition, reason):
    if not condition:
        raise UnoConstructionRefused(reason)


def _sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def _canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',', ':'),
                       ensure_ascii=True,allow_nan=False)+'\n').encode()


def _decode(raw):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            need(key not in out, 'ordinary_uno_duplicate_transport_key')
            out[key] = value
        return out
    def constant(_):
        raise UnoConstructionRefused('ordinary_uno_nonfinite_transport')
    try:
        return json.loads(raw,object_pairs_hook=unique,parse_constant=constant)
    except (TypeError,ValueError,UnicodeError) as exc:
        if isinstance(exc,UnoConstructionRefused):
            raise
        raise UnoConstructionRefused('ordinary_uno_invalid_transport') from None


def _stamp(s):
    return (s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode,s.st_nlink,
            s.st_size,s.st_mtime_ns,s.st_ctime_ns)


def _read_private(path, limit):
    fd = os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
             and before.st_nlink == 1 and not before.st_mode & 0o077
             and 0 < before.st_size <= limit, 'ordinary_uno_private_transport_required')
        chunks, size = [], 0
        while True:
            chunk = os.read(fd,min(65536,limit+1-size))
            if not chunk:
                break
            chunks.append(chunk); size += len(chunk)
            need(size <= limit,'ordinary_uno_transport_size')
        need(size == before.st_size and _stamp(before) == _stamp(os.fstat(fd))
             == _stamp(Path(path).stat(follow_symlinks=False)),
             'ordinary_uno_transport_changed')
        return b''.join(chunks)
    finally:
        os.close(fd)


def validate_config(c):
    """Shape/finite binding only, never a substitute for actual observations."""
    need(type(c) is dict and set(c) == _CONFIG_FIELDS and c['schema'] == SCHEMA,
         'ordinary_uno_exact_config_required')
    need(type(c['nonce']) is str and re.fullmatch('[0-9a-f]{32}',c['nonce']) is not None
         and c['pipe_name'] == 'friday_metric_'+c['nonce'], 'ordinary_uno_owned_pipe_required')
    need(_sha(c['source_sha256']) and type(c['source_bytes']) is int
         and 0 < c['source_bytes'] <= 1000000, 'ordinary_uno_original_source_required')
    p, s = c['process'], c['symbols']
    need(type(p) is dict and set(p) == {'pid','start_ticks','gdb_pid','inferior'}
         and all(type(v) is int and v > 0 for v in p.values()) and p['inferior'] == 1
         and p['pid'] > 1 and p['gdb_pid'] > 1 and p['pid'] != p['gdb_pid'],
         'ordinary_uno_process_identity_required')
    need(type(s) is dict and set(s) == {'outer','native','native_return'}
         and all(type(v) is int and v > 0 for v in s.values()),
         'ordinary_uno_native_symbols_required')
    start, parent, deadline = (c[k] for k in
                              ('started_monotonic','parent_deadline','deadline'))
    need(all(type(v) in (int,float) and math.isfinite(v) and v > 0
             for v in (start,parent,deadline)) and start < deadline <= parent
         and deadline <= start+35, 'ordinary_uno_absolute_child_deadline_required')
    return c


def _guard(c):
    need(c['started_monotonic'] <= time.monotonic() < c['deadline'],
         'ordinary_uno_deadline_expired')
    need(not os.path.lexists(WORK/'ordinary-cancel'), 'ordinary_uno_cancelled')


def _source(c):
    raw = _read_private(WORK/'input.ods',1000000)
    need(len(raw) == c['source_bytes']
         and hashlib.sha256(raw).hexdigest() == c['source_sha256'],
         'ordinary_uno_dynamic_source_changed')


def _proc_fields(raw):
    """Stat comm may contain spaces and ')' characters; split at final ')' only."""
    try:
        fields = raw.rsplit(')',1)[1].split()
        return fields[0], int(fields[1]), int(fields[19])
    except (IndexError,ValueError):
        raise UnoConstructionRefused('ordinary_uno_invalid_process_stat') from None


def _target_argv(c):
    return (str(PROGRAM/'soffice.bin'),
            '-env:UserInstallation='+(WORK/'profile').as_uri(),
            '--headless','--nologo','--norestore','--nodefault','--nofirststartwizard',
            '--accept=pipe,name='+c['pipe_name']+';urp;StarOffice.ComponentContext')


def target_environment():
    """Closed fixed launch source expression, never transport/caller supplied."""
    w,p = str(WORK),str(PROGRAM)
    return {'HOME':w+'/tmp','TMPDIR':w+'/tmp','XDG_CACHE_HOME':w+'/cache',
        'XDG_CONFIG_HOME':w+'/config','XDG_RUNTIME_DIR':w+'/runtime',
        'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','PATH':'/usr/bin:/bin',
        'SAL_USE_VCLPLUGIN':'svp',
        'LD_LIBRARY_PATH':w+'/code/uno/program:'+p+
            ':/opt/friday-document-toolchain/root/usr/lib/x86_64-linux-gnu',
        'URE_BOOTSTRAP':'vnd.sun.star.pathname:'+p+'/fundamentalrc',
        'PYTHONDONTWRITEBYTECODE':'1'}


def _verify_target_snapshot(c, snapshot):
    """Exact pure observation reducer, also exercised with SOURCE fake leaves."""
    need(type(snapshot) is dict and set(snapshot) ==
         {'state','parent','start_ticks','exe','argv','environment','namespaces',
          'self_namespaces','gdb_parent','gdb_exe'}, 'ordinary_uno_target_snapshot_required')
    p = c['process']
    need(snapshot['state'] not in ('Z','X','x') and snapshot['start_ticks'] == p['start_ticks']
         and snapshot['parent'] == p['gdb_pid'] and snapshot['gdb_parent'] == 1,
         'ordinary_uno_target_birth_or_parent_changed')
    need(snapshot['exe'] == str(PROGRAM/'soffice.bin')
         and snapshot['gdb_exe'] == '/usr/bin/gdb' and tuple(snapshot['argv']) == _target_argv(c),
         'ordinary_uno_stock_owned_launch_changed')
    env = snapshot['environment']
    need(type(env) is dict and env == target_environment(),
         'ordinary_uno_target_start_environment_changed')
    need(type(snapshot['namespaces']) is dict
         and set(snapshot['namespaces']) == {'pid','mnt','net','user'}
         and snapshot['namespaces'] == snapshot['self_namespaces'],
         'ordinary_uno_target_namespace_changed')
    return {'LC_ALL':'C.UTF-8'}


def _observe_target(c):
    """Called only inside the real entry, never during source inspection/tests."""
    _guard(c)
    p = c['process']; base = Path('/proc')/str(p['pid'])
    state, parent, start = _proc_fields((base/'stat').read_text())
    gdb = Path('/proc')/str(p['gdb_pid'])
    _, gdb_parent, _ = _proc_fields((gdb/'stat').read_text())
    raw_env = (base/'environ').read_bytes()
    need(len(raw_env) <= 65536, 'ordinary_uno_environment_size')
    env = {}
    try:
        for item in raw_env.rstrip(b'\0').split(b'\0'):
            key, value = item.split(b'=',1)
            key, value = key.decode('ascii'), value.decode('utf-8')
            need(key not in env,'ordinary_uno_duplicate_environment_key')
            env[key] = value
        argv = tuple(x.decode('utf-8') for x in (base/'cmdline').read_bytes().rstrip(b'\0').split(b'\0'))
    except (ValueError,UnicodeError):
        raise UnoConstructionRefused('ordinary_uno_invalid_process_environment') from None
    names = ('pid','mnt','net','user')
    snapshot = dict(state=state,parent=parent,start_ticks=start,exe=os.readlink(base/'exe'),
        argv=argv,environment=env,gdb_parent=gdb_parent,gdb_exe=os.readlink(gdb/'exe'),
        namespaces={n:os.readlink(base/'ns'/n) for n in names},
        self_namespaces={n:os.readlink('/proc/self/ns/'+n) for n in names})
    _verify_target_snapshot(c,snapshot)
    _, parent_after, start_after = _proc_fields((base/'stat').read_text())
    need((parent,start) == (parent_after,start_after), 'ordinary_uno_target_changed_during_observation')
    _guard(c)
    return snapshot


def _stable_target(snapshot):
    # Scheduler/ptrace state is live and may change between two observations.
    # All birth/ancestry/exec/argv/env/namespace fields must remain identical.
    return {key:value for key,value in snapshot.items() if key != 'state'}


def _read_managed(path, expected):
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
         and before.st_nlink == 1 and not before.st_mode & 0o022
         and 0 < before.st_size <= 2097152 and path.resolve() == path,
         'ordinary_uno_managed_binding_required')
    fd = os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        need(_stamp(before) == _stamp(os.fstat(fd)), 'ordinary_uno_binding_open_race')
        with os.fdopen(fd,'rb',closefd=False) as stream:
            actual = hashlib.file_digest(stream,'sha256').hexdigest()
        need(actual == expected and _stamp(before) == _stamp(os.fstat(fd))
             == _stamp(path.lstat()), 'ordinary_uno_binding_changed')
    finally:
        os.close(fd)


def _import_managed_uno():
    need(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode,
         'ordinary_uno_isolated_I_B_S_required')
    need(not any(name in sys.modules for name in ('uno','unohelper','pyuno','com.sun.star.task')),
         'ordinary_uno_binding_already_imported')
    for relative, expected in UNO_FILES:
        _read_managed(CODE/relative,expected)
    sys.path[0:0] = [str(CODE/'uno/python'),str(CODE/'uno/program')]
    import uno
    import unohelper
    import pyuno
    from com.sun.star.task import XInteractionHandler
    for module, relative in ((uno,'uno/python/uno.py'),(unohelper,'uno/python/unohelper.py'),
                             (pyuno,'uno/program/pyuno.so')):
        need(Path(module.__file__).resolve() == CODE/relative,
             'ordinary_uno_imported_binding_path_changed')
    for relative, expected in UNO_FILES:
        _read_managed(CODE/relative,expected)
    paths = {line.split(None,5)[5].strip() for line in Path('/proc/self/maps').read_text().splitlines()
             if len(line.split(None,5)) == 6}
    need(str(CODE/'uno/program/libpyuno.so') in paths,
         'ordinary_uno_actual_libpyuno_mapping_required')
    need(type(uno.getConstantByName('com.sun.star.document.MacroExecMode.NEVER_EXECUTE')) is int
         and uno.getConstantByName('com.sun.star.document.MacroExecMode.NEVER_EXECUTE') == 0
         and type(uno.getConstantByName('com.sun.star.document.UpdateDocMode.NO_UPDATE')) is int
         and uno.getConstantByName('com.sun.star.document.UpdateDocMode.NO_UPDATE') == 0,
         'ordinary_uno_actual_load_constants_changed')
    return uno,unohelper,XInteractionHandler


def _abort_interaction(handler, request, abort_type):
    handler.requests += 1
    for continuation in request.getContinuations():
        abort = continuation.queryInterface(abort_type)
        if abort is not None:
            abort.select(); handler.aborts_selected += 1
            return
    raise UnoConstructionRefused('ordinary_uno_interaction_without_abort')


def _descriptor_values(values):
    need(type(values) is dict and set(values) == set(_DESCRIPTOR_TYPES)
         and all(type(values[k]) is kind for k,kind in _DESCRIPTOR_TYPES.items()),
         'ordinary_uno_descriptor_schema')
    need(re.fullmatch(r'[A-Za-z0-9 ._()+-]{1,128}',values['Name']) is not None
         and values['Height'] == 220 and values['Family'] == 5 and values['CharSet'] in (0,1)
         and values['Weight'] == 100.0 and values['StyleName'] == '' and values['Width'] == 0
         and values['CharacterWidth'] == 0.0 and values['Pitch'] == 0 and values['Slant'] == 'NONE'
         and values['Underline'] == 0 and values['Strikeout'] == 0 and values['Orientation'] == 0.0
         and values['Kerning'] is True and values['WordLineMode'] is False and values['Type'] == 0,
         'ordinary_uno_descriptor_outside_clean_profile')
    need(all(math.isfinite(values[k]) for k in ('CharacterWidth','Weight','Orientation')),
         'ordinary_uno_nonfinite_descriptor')
    return values


@dataclass(frozen=True)
class _OwnedRuntimeState:
    config: dict
    local: object
    remote: object
    desktop: object
    handler: object
    initial_target: dict


def construct_runtime(c):
    """Actual fixed constructor; there is no caller-supplied service/factory."""
    validate_config(c); _guard(c); _source(c)
    need(os.getppid() == 1, 'ordinary_uno_sole_namespace_supervisor_required')
    snapshot = _observe_target(c)
    uno,unohelper,handler_type = _import_managed_uno()
    local = uno.getComponentContext()
    need(local is not None, 'ordinary_uno_local_bootstrap_context_missing')
    resolver = local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local)
    need(resolver is not None, 'ordinary_uno_resolver_missing')
    endpoint = 'uno:pipe,name='+c['pipe_name']+';urp;StarOffice.ComponentContext'
    remote = None
    # No relative subclock. Every retry uses the same startup->terminal deadline.
    while remote is None:
        _guard(c); _observe_target(c)
        try:
            remote = resolver.resolve(endpoint)
        except Exception:
            _guard(c); time.sleep(min(.025,max(0,c['deadline']-time.monotonic())))
    need(remote is not local, 'ordinary_uno_real_remote_context_required')
    _guard(c); _observe_target(c)
    desktop = remote.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',remote)
    need(desktop is not None, 'ordinary_uno_remote_desktop_missing')
    abort_type = uno.getTypeByName('com.sun.star.task.XInteractionAbort')

    class AbortOnly(unohelper.Base,handler_type):
        def __init__(self):
            self.requests = 0
            self.aborts_selected = 0

        def handle(self,request):
            return _abort_interaction(self,request,abort_type)

    handler = AbortOnly()

    def property_value(name,value):
        _guard(c)
        need(type(name) is str and name in {'Hidden','ReadOnly','MacroExecutionMode','UpdateDocMode',
             'FilterName','InteractionHandler','Overwrite','ConversionRequestOrigin','nodepath'},
             'ordinary_uno_property_name_unsupported')
        if name in ('MacroExecutionMode','UpdateDocMode'):
            need(type(value) is int and value == 0, 'ordinary_uno_typed_short_zero_required')
            selected = uno.Any('short',value)
            need(selected.type.typeName == 'short' and type(selected.value) is int and selected.value == 0,
                 'ordinary_uno_typed_short_changed')
        else:
            allowed = (
                name in ('Hidden','ReadOnly','Overwrite') and value is True
                or name == 'FilterName' and type(value) is str
                   and value in ('calc8','Calc MS Excel 2007 XML')
                or name == 'InteractionHandler' and value is handler
                or name == 'ConversionRequestOrigin' and value == 'CommandLine'
                   and type(value) is str
                or name == 'nodepath' and type(value) is str and value in (
                    '/org.openoffice.Setup/L10N','/org.openoffice.VCL/FontSubstitutions')
            )
            need(allowed,'ordinary_uno_property_value_unsupported')
            selected = value
        prop = uno.createUnoStruct('com.sun.star.beans.PropertyValue')
        need(getattr(type(prop),'__pyunostruct__',None) == 'com.sun.star.beans.PropertyValue',
             'ordinary_uno_PropertyValue_type_changed')
        prop.Name = name; prop.Value = selected
        return prop

    def descriptor_factory(values):
        _guard(c); _descriptor_values(values)
        descriptor = uno.createUnoStruct('com.sun.star.awt.FontDescriptor')
        need(getattr(type(descriptor),'__pyunostruct__',None) == 'com.sun.star.awt.FontDescriptor',
             'ordinary_uno_FontDescriptor_type_changed')
        for name,value in values.items():
            if name == 'Slant':
                value = uno.Enum('com.sun.star.awt.FontSlant','NONE')
                need(value.typeName == 'com.sun.star.awt.FontSlant' and value.value == 'NONE',
                     'ordinary_uno_FontSlant_enum_changed')
            setattr(descriptor,name,value)
        need(all((getattr(descriptor,k).value if k == 'Slant' else getattr(descriptor,k)) == v
                 and (k == 'Slant' or type(getattr(descriptor,k)) is type(v)) for k,v in values.items()),
             'ordinary_uno_typed_descriptor_changed')
        return descriptor

    runtime = dict(desktop=desktop,handler=handler,property_value_factory=property_value,
        descriptor_factory=descriptor_factory,remote_context=remote,local_context=local,
        startup_locale_environment={'LC_ALL':'C.UTF-8'},stock_startup_locale_lifecycle=None)
    # The locale lemma is deliberately not granted by a local context, endpoint,
    # connection or config value. The actual single successful load is required.
    runtime['_ordinary_state'] = _OwnedRuntimeState(c,local,remote,desktop,handler,snapshot)
    _guard(c); _source(c); _observe_target(c)
    return runtime


def bind_loaded_lifecycle(runtime,doc,*,work,nonce,process,symbols,source_sha256,source_bytes,deadline):
    """Called by fixed factory loaded barrier after the actual single safe load.

    The enabled normal bridge + Desktop + successful admitted load establish the
    pinned Desktop::prepareLocale control-flow lemma, under supervisor-owned
    stock/source/config/exclusive-history custody. No JSON boolean grants it.
    """
    need(type(runtime) is dict and type(runtime.get('_ordinary_state')) is _OwnedRuntimeState,
         'ordinary_uno_owned_runtime_required')
    state = runtime['_ordinary_state']; c = state.config
    need(Path(work) == WORK and nonce == c['nonce'] and process == c['process']
         and symbols == c['symbols'] and source_sha256 == c['source_sha256']
         and source_bytes == c['source_bytes'] and deadline == c['deadline'],
         'ordinary_uno_loaded_operation_changed')
    need(runtime['local_context'] is state.local and runtime['remote_context'] is state.remote
         and state.local is not state.remote and runtime['desktop'] is state.desktop
         and runtime['handler'] is state.handler and type(state.handler.requests) is int
         and state.handler.requests == 0, 'ordinary_uno_loaded_runtime_changed')
    _guard(c); _source(c)
    current = _observe_target(c)
    need(_stable_target(current) == _stable_target(state.initial_target),
         'ordinary_uno_loaded_target_changed')
    need(doc is not None and doc.supportsService('com.sun.star.sheet.SpreadsheetDocument') is True
         and doc.getURL() == (WORK/'input.ods').as_uri() and doc.isReadonly() is True
         and doc.isModified() is False, 'ordinary_uno_safe_load_required')
    need(runtime['stock_startup_locale_lifecycle'] is None,
         'ordinary_uno_locale_lifecycle_already_bound')
    runtime['stock_startup_locale_lifecycle'] = LIFECYCLE


def _write_result(value):
    path = WORK/'ordinary-inner-result.json'
    raw = _canonical(value)
    need(len(raw) <= 262144,'ordinary_uno_result_size')
    fd = os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    with os.fdopen(fd,'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def run_inner():
    """No path/module/profile arguments; only sole supervisor's fixed transport."""
    need(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode,
         'ordinary_uno_isolated_I_B_S_required')
    need(Path(__file__).resolve() == CODE/'hermes_cli/friday_workspace_calc_native_uno.py'
         and os.getppid() == 1, 'ordinary_uno_managed_entry_required')
    c = validate_config(_decode(_read_private(CONFIG,16384)))
    _guard(c); _source(c)
    # In isolated -S mode the entry directory is intentionally not added by
    # Python. Add only this exact RO generation, never supplied transport paths.
    sys.path.insert(0,str(CODE))
    # The source file is executed as __main__. Factory imports must use this
    # very module/class identity rather than creating a second state class.
    module_name = 'hermes_cli.friday_workspace_calc_native_uno'
    need(module_name not in sys.modules or sys.modules[module_name] is sys.modules[__name__],
         'ordinary_uno_entry_module_already_imported')
    sys.modules[module_name] = sys.modules[__name__]
    from hermes_cli.friday_workspace_calc_measured import produce_on_remote
    runtime = construct_runtime(c)
    candidate = produce_on_remote(runtime,work=WORK,source_sha256=c['source_sha256'],
        source_bytes=c['source_bytes'],nonce=c['nonce'],process=c['process'],
        symbols=c['symbols'],deadline=c['deadline'])
    _guard(c); _source(c)
    # Candidate only. Terminal native/helper/process closure is still mandatory
    # after this child and owned target have actually exited and been reaped.
    _write_result(candidate)
    return 0


def main():
    need(len(sys.argv) == 1,'ordinary_uno_no_external_arguments')
    try:
        return run_inner()
    except BaseException:
        # Supervisor retains actual failure/cleanup observation. Never expose
        # arbitrary UNO exception messages, user content or config in stderr.
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
