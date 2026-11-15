"""Finite future Root inner Office client. Import/--inspect never imports UNO.

Only Root's separately admitted supervisor may execute this in the SAME private
namespace as GDB and its direct soffice.bin child. A hash authenticates bytes,
not authority. All outputs remain candidates; outer native join, unchanged source
and whole-own-tree cleanup are mandatory. This module creates no admission.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import time

SCHEMA = 'frw.calc.inner-input.v1'
WORK = '/tmp/friday-metric-work'
SCALARS = dict(Hidden=True, ReadOnly=True, MacroExecutionMode=0, UpdateDocMode=0)
START_ENV = {'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'}


class Refused(ValueError):
    pass


def need(ok, reason):
    if not ok:
        raise Refused(reason)


def digest(v):
    return type(v) is str and re.fullmatch('[0-9a-f]{64}', v) is not None


def canonical(v):
    return (json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def unique(pairs):
    result = {}
    for k, v in pairs:
        need(k not in result, 'duplicate_JSON_key')
        result[k] = v
    return result


def decode(raw):
    def constant(_):
        raise Refused('nonfinite_JSON')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=constant)


def exact(v, keys, why):
    need(type(v) is dict and set(v) == set(keys), why)


def safe_path(value):
    need(type(value) is str and 0 < len(value) <= 4096 and '\x00' not in value,
         'absolute_canonical_path_required')
    p = Path(value)
    need(p.is_absolute() and '..' not in p.parts and str(p) == value,
         'absolute_canonical_path_required')
    return p


def protected_bytes(path, expected=None, *, limit=1048576):
    """No symlinks; current UID, one link, no group/other rights or owner write
    requirement. Both honest read-only0400 and private0600 records are accepted.
    Ancestor ownership/mount custody belongs to the outer namespace admission.
    """
    p = safe_path(path)
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        s = os.fstat(fd)
        need(stat.S_ISREG(s.st_mode) and s.st_uid == os.getuid() and s.st_nlink == 1
             and not (s.st_mode & 0o077) and s.st_size <= limit, 'protected_file_required')
        chunks = []
        remaining = limit + 1
        while remaining:
            b = os.read(fd, min(65536, remaining))
            if not b:
                break
            chunks.append(b)
            remaining -= len(b)
        raw = b''.join(chunks)
        after = os.fstat(fd)
        need(len(raw) <= limit and (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
             == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
             'file_changed_during_read')
    finally:
        os.close(fd)
    if expected is not None:
        need(digest(expected) and hashlib.sha256(raw).hexdigest() == expected, 'file_pin_changed')
    return raw


def read_ref(ref, *, limit=1048576):
    exact(ref, ('path', 'sha256'), 'exact_file_ref_required')
    return protected_bytes(ref['path'], ref['sha256'], limit=limit)


def atomic_json(path, value):
    """Declared own metadata effect, same-directory exclusive temp+rename+fsync."""
    p = safe_path(path)
    parent = p.parent
    s = parent.stat(follow_symlinks=False)
    need(stat.S_ISDIR(s.st_mode) and s.st_uid == os.getuid() and not (s.st_mode & 0o077),
         'private_metadata_parent_required')
    need(not p.is_symlink(), 'metadata_symlink_refused')
    tmp = parent / ('.' + p.name + '.inner-' + str(os.getpid()))
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        data = canonical(value)
        while data:
            data = data[os.write(fd, data):]
        os.fsync(fd)
    finally:
        os.close(fd)
    try:
        os.replace(tmp, p)
        directory = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if tmp.exists():
            tmp.unlink()


def validate_config(c, *, allow_unstarted=False):
    exact(c, ('schema', 'operation_id', 'nonce', 'pipe_name', 'office_process', 'modules', 'uno',
              'preload', 'handler_source_ref', 'paths', 'timeouts'), 'exact_inner_input_required')
    need(c['schema'] == SCHEMA, 'inner_schema_required')
    need(type(c['operation_id']) is str and re.fullmatch('[A-Za-z0-9_.-]{1,128}', c['operation_id']),
         'operation_id_required')
    need(type(c['nonce']) is str and re.fullmatch('[0-9a-f]{32}', c['nonce']), 'fresh_nonce_shape_required')
    need(type(c['pipe_name']) is str and re.fullmatch('[A-Za-z0-9_-]{16,128}', c['pipe_name']),
         'private_pipe_name_required')
    p = c['office_process']
    if not (allow_unstarted and p is None):
        exact(p, ('namespace_pid', 'start_ticks', 'executable_sha256'), 'office_identity_required')
        need(type(p['namespace_pid']) is int and p['namespace_pid'] > 0 and type(p['start_ticks']) is int
             and p['start_ticks'] > 0 and digest(p['executable_sha256']), 'office_identity_UNBOUND')
    exact(c['modules'], ('qualifier', 'resolver', 'leaf'), 'three_modules_required')
    for r in list(c['modules'].values()) + [c['preload'], c['handler_source_ref']]:
        exact(r, ('path', 'sha256'), 'exact_file_ref_required')
        safe_path(r['path'])
        need(digest(r['sha256']), 'file_pin_UNBOUND')
    u = c['uno']
    exact(u, ('search_paths', 'files'), 'explicit_UNO_binding_required')
    need(type(u['search_paths']) is list and len(u['search_paths']) == 3
         and len(set(u['search_paths'])) == 3, 'exact_three_UNO_paths_required')
    for path in u['search_paths']:
        safe_path(path)
    need(type(u['files']) is list and len(u['files']) == 4, 'exact_four_UNO_files_required')
    need({Path(x['path']).name for x in u['files']} == {'uno.py', 'unohelper.py', 'pyuno.so', 'libpyuno.so'},
         'four_UNO_members_required')
    for r in u['files']:
        exact(r, ('path', 'sha256'), 'exact_UNO_file_ref_required')
        safe_path(r['path'])
        need(digest(r['sha256']), 'UNO_file_pin_UNBOUND')
    paths = c['paths']
    exact(paths, ('work', 'phase', 'trace', 'checkpoint', 'loaded_envelope', 'started'), 'private_paths_required')
    need(paths['work'] == WORK, 'fixed_namespace_work_required')
    for path in paths.values():
        p = safe_path(path)
        need(str(p) == WORK or (p.parent == Path(WORK)), 'direct_owned_work_child_required')
    need(len(set(paths.values())) == len(paths), 'distinct_inner_paths_required')
    exact(c['timeouts'], ('connect_seconds', 'loaded_seconds', 'ready_seconds'), 'bounded_inner_timeouts_required')
    for v in c['timeouts'].values():
        need(type(v) in (int, float) and 0 < v <= 180, 'finite_inner_timeout_required')
    return c


def load_modules(c):
    """Pinned source only; no UNO import. Reviewed modules have inert top levels."""
    result = {}
    for role, ref in c['modules'].items():
        raw = read_ref(ref)
        code = compile(raw, ref['path'], 'exec')
        namespace = {'__name__': 'frw_pinned_' + role, '__file__': ref['path']}
        exec(code, namespace)
        result[role] = namespace
    return result


def inspect_inputs(c, *, _unstarted=False):
    """Outer calls BEFORE starting Office. Real preload refusal precedes effects.
    Does read only explicit protected source/preload metadata; no /proc/UNO.
    """
    validate_config(c, allow_unstarted=_unstarted)
    m = load_modules(c)
    raw = read_ref(c['preload'], limit=262144)
    pre, pre_sha = m['qualifier']['decode_root_record'](raw, c['preload']['sha256'])
    m['qualifier']['validate_preload_inputs'](pre, pre_sha)
    need(pre['operation_id'] == c['operation_id'], 'preload_operation_mismatch')
    need(str(Path(__file__).resolve()) == c['handler_source_ref']['path'], 'actual_handler_source_path_required')
    read_ref(c['handler_source_ref'])
    for binding in c['uno']['files']:
        read_ref(binding, limit=2097152)
    return m, pre, pre_sha


def inspect_prelaunch(c):
    """No Office PID exists yet: ONLY this static API admits office_process=None.
    Real execute/full inspect must receive actual readiness PID/birth afterwards.
    """
    return inspect_inputs(c, _unstarted=True)


def proc_identity(c):
    """Actual same-namespace process observation, repeated at each live boundary."""
    expected = c['office_process']
    base = Path('/proc') / str(expected['namespace_pid'])
    raw = (base / 'stat').read_text().rsplit(')', 1)[1].split()
    need(int(raw[19]) == expected['start_ticks'], 'Office_birth_changed')
    exe = base / 'exe'
    with exe.open('rb') as f:
        actual = hashlib.file_digest(f, 'sha256').hexdigest()
    need(actual == expected['executable_sha256'], 'Office_executable_changed')
    self_namespaces = {n: os.readlink('/proc/self/ns/' + n) for n in ('pid', 'mnt', 'net', 'user')}
    office_namespaces = {n: os.readlink(str(base / 'ns' / n)) for n in self_namespaces}
    need(self_namespaces == office_namespaces, 'client_Office_namespace_mismatch')
    return dict(expected, executable_path=os.readlink(exe), namespaces=office_namespaces,
                observed_parent_namespace_pid=int(raw[1]))


def wait_json(path, timeout, predicate):
    deadline = time.monotonic() + timeout
    while True:
        try:
            value = decode(protected_bytes(path))
        except FileNotFoundError:
            value = None
        if value is not None and predicate(value):
            return value
        need(time.monotonic() < deadline, 'bounded_metadata_wait_expired')
        time.sleep(min(0.025, max(0, deadline - time.monotonic())))


def verify_ready(value, c):
    need(type(value) is dict and value.get('schema') == 'frw.native-return-trace.v1'
         and value.get('nonce') == c['nonce'] and value.get('kind') == 'OFFICE_UNADMITTED',
         'native_trace_identity_required')
    need(value.get('error') is None and value.get('status') not in ('REFUSED', 'UNKNOWN'),
         'native_observer_refused')
    if value.get('status') != 'READY_UNRELEASED':
        return False
    p = value.get('process')
    need(type(p) is dict and type(p.get('pid')) is int and type(p.get('start_ticks')) is int
         and p.get('pid') == c['office_process']['namespace_pid']
         and p.get('start_ticks') == c['office_process']['start_ticks'], 'native_process_mismatch')
    need(value.get('records') == [], 'native_observer_not_fresh')
    return True


class PhaseCallbacks:
    def __init__(self, c, write=atomic_json, read=None):
        self.c = c
        self.write = write
        self.read = read or (lambda p: decode(protected_bytes(p)))
        self.responses = []
        self.active = None

    def before(self, index, digit):
        need(self.active is None and type(index) is int and index == len(self.responses)
             and 0 <= index < 10 and digit == str(index), 'ordered_single_metric_required')
        self.active = dict(nonce=self.c['nonce'], phase='METRIC', index=index, digit=digit)
        self.write(self.c['paths']['phase'], self.active)

    def after(self, index, digit, raw32):
        need(self.active == dict(nonce=self.c['nonce'], phase='METRIC', index=index, digit=digit)
             and self.read(self.c['paths']['phase']) == self.active, 'phase_changed_during_UNO_call')
        need(type(raw32) is int and -(2**31) <= raw32 < 2**31, 'raw32_transport_required')
        self.responses.append(dict(index=index, digit=digit, raw32=raw32))
        self.active = None  # The published METRIC remains unchanged through return.

    def closed(self):
        need(self.active is None and len(self.responses) == 10, 'ten_completed_calls_before_CLOSED_required')
        self.write(self.c['paths']['phase'], dict(nonce=self.c['nonce'], phase='CLOSED', index=None, digit=None))


def abort_interaction(handler, request, abort_type):
    """Only XInteractionAbort can be selected; count even an unhandled request.
    Pure protocol controls call this exact leaf with inert continuations.
    """
    handler.requests += 1
    for continuation in request.getContinuations():
        abort = continuation.queryInterface(abort_type)
        if abort is not None:
            abort.select()
            handler.aborts_selected += 1
            return
    raise RuntimeError('interaction_without_abort_continuation')


def real_runtime(c):
    """ONLY real future execution leaf; source-inspectable, no local/remote swap."""
    need(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode,
         'isolated_I_B_S_required')
    for r in c['uno']['files']:
        read_ref(r, limit=2097152)
    need('uno' not in sys.modules and 'pyuno' not in sys.modules and 'unohelper' not in sys.modules,
         'UNO_binding_already_imported')
    sys.path[0:0] = c['uno']['search_paths']
    import uno
    import unohelper
    import pyuno
    from com.sun.star.task import XInteractionHandler
    expected = {Path(r['path']).name: r for r in c['uno']['files']}
    for module, basename in ((uno, 'uno.py'), (unohelper, 'unohelper.py'), (pyuno, 'pyuno.so')):
        need(str(Path(module.__file__).resolve()) == expected[basename]['path'], 'imported_UNO_path_changed')
        read_ref(expected[basename], limit=2097152)
    mapped_paths = {line.split(None, 5)[5].strip() for line in Path('/proc/self/maps').read_text().splitlines()
                    if len(line.split(None, 5)) == 6 and line.split(None, 5)[5].strip().startswith('/')}
    need(expected['libpyuno.so']['path'] in mapped_paths, 'actual_libpyuno_mapping_required')
    need(uno.getConstantByName('com.sun.star.document.MacroExecMode.NEVER_EXECUTE') == 0
         and uno.getConstantByName('com.sun.star.document.UpdateDocMode.NO_UPDATE') == 0,
         'actual_UNO_load_constants_changed')
    local_ctx = uno.getComponentContext()  # ONLY resolver construction, never Office config.
    resolver = local_ctx.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', local_ctx)
    endpoint = 'uno:pipe,name=' + c['pipe_name'] + ';urp;StarOffice.ComponentContext'
    deadline = time.monotonic() + c['timeouts']['connect_seconds']
    remote_ctx = None
    while remote_ctx is None:
        try:
            remote_ctx = resolver.resolve(endpoint)
        except Exception:
            need(time.monotonic() < deadline, 'private_Office_pipe_connect_timeout')
            time.sleep(0.025)
    need(remote_ctx is not None and remote_ctx is not local_ctx, 'real_remote_Office_context_required')
    desktop = remote_ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop', remote_ctx)
    need(desktop is not None, 'remote_Office_desktop_required')
    abort_type = uno.getTypeByName('com.sun.star.task.XInteractionAbort')

    class AbortOnly(unohelper.Base, XInteractionHandler):
        def __init__(self):
            self.requests = 0
            self.aborts_selected = 0
            self.instance_token = 'inner-' + c['nonce']

        def handle(self, request):
            # Even successfully aborted requests refuse the load: count must be0.
            return abort_interaction(self, request, abort_type)

    def pv(name, value):
        p = uno.createUnoStruct('com.sun.star.beans.PropertyValue')
        p.Name = name
        # MediaDescriptor declares both as short and Sfx appuno.cxx extracts
        # sal_Int16. Do not rely on Python integer -> Any<long> coercion.
        p.Value = uno.Any('short', value) if name in ('MacroExecutionMode', 'UpdateDocMode') else value
        return p

    return dict(remote_context=remote_ctx, desktop=desktop, handler=AbortOnly(),
                property_value_factory=pv, descriptor_factory=None, endpoint=endpoint,
                binding_observations=dict(uno_module=uno.__file__, unohelper_module=unohelper.__file__,
                                          pyuno_module=pyuno.__file__, libpyuno_mapping=expected['libpyuno.so']['path']))


def load_actual_envelope(c, pre, modules):
    def accepts(v):
        exact(v, ('schema', 'operation_id', 'nonce', 'record'), 'loaded_envelope_schema_required')
        need(v['schema'] == 'frw.calc.inner.loaded-envelope.v1' and v['operation_id'] == c['operation_id']
             and v['nonce'] == c['nonce'], 'loaded_envelope_identity_required')
        return True
    envelope = wait_json(c['paths']['loaded_envelope'], c['timeouts']['loaded_seconds'], accepts)
    need(safe_path(envelope['record']['path']).parent == Path(WORK), 'loaded_record_owned_work_required')
    raw = read_ref(envelope['record'], limit=262144)
    loaded, sha = modules['qualifier']['decode_root_record'](raw, envelope['record']['sha256'])
    modules['qualifier']['validate_loaded_facts'](loaded, sha, pre)
    return loaded, sha


def claim_started(c):
    need(not os.path.lexists(c['paths']['loaded_envelope']), 'prefilled_future_loaded_facts_refused')
    fd = os.open(c['paths']['started'], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        data = canonical(dict(operation_id=c['operation_id'], nonce=c['nonce']))
        while data:
            data = data[os.write(fd, data):]
        os.fsync(fd)
    finally:
        os.close(fd)


def execute_inner(c, *, modules=None, preload=None, runtime_factory=real_runtime,
                  identity_observer=proc_identity, loaded_supplier=load_actual_envelope,
                  readiness=None, write=atomic_json, phase_callbacks=None, claim=claim_started):
    """Real finite orchestration. Tests inject EXPLICIT inert leaves, never PASS.
    Call only after outer admission/static preflight. Any blocking UNO call is
    bounded by outer hard deadline/cgroup cleanup; in-process clocks cannot cancel
    a synchronous native call. No inner timeout is represented as tree custody.
    """
    validate_config(c)
    need(all(os.environ.get(k) == v for k, v in START_ENV.items()), 'C_UTF8_start_environment_required')
    if modules is None:
        modules, pre, pre_sha = inspect_inputs(c)
    else:
        need(preload is not None, 'explicit_inert_preload_required')
        pre, pre_sha = preload
        modules['qualifier']['validate_preload_inputs'](pre, pre_sha)
    claim(c)  # A future loaded record may NOT exist before this real load.
    observe_ready = readiness or (lambda: wait_json(c['paths']['trace'], c['timeouts']['ready_seconds'],
                                                    lambda value: verify_ready(value, c)))
    observe_ready()
    identity = identity_observer(c)
    phases = phase_callbacks or PhaseCallbacks(c, write=write)
    result = dict(schema='frw.calc.inner-result.v1', operation_id=c['operation_id'], nonce=c['nonce'],
                  status='REFUSED', stage='PRECONNECT', candidate=None, actual_M=None,
                  runtime_attested=False, actual_case_accepted=False, physical_fidelity='UNASSESSED',
                  readonly_close_confirmed=False, desktop_terminate_requested=False,
                  handler_requests=None, error=None, office_process=identity,
                  native_join='UNBOUND_OUTER', source_hashes='UNBOUND_OUTER_POSTCLOSE',
                  whole_owned_tree_cleanup='UNBOUND_OUTER')
    runtime = None
    doc = None
    close_attempted = False
    terminate_attempted = False
    try:
        runtime = runtime_factory(c)
        result['binding_observations'] = runtime.get('binding_observations')
        handler, pv = runtime['handler'], runtime['property_value_factory']
        args = tuple(pv(k, v) for k, v in SCALARS.items()) + (pv('InteractionHandler', handler),)
        result['stage'] = 'LOAD'
        doc = runtime['desktop'].loadComponentFromURL(pre['working_copy']['url'], '_blank', 0, args)
        need(doc is not None and handler.requests == 0, 'load_or_interaction_refused')
        load_request = dict(url=pre['working_copy']['url'], scalar_arguments=SCALARS.copy(),
                            interaction_requests=handler.requests,
                            interaction_handler=dict(argument_name='InteractionHandler', kind='ABORT_ONLY',
                                instance_token=handler.instance_token, source_ref=c['handler_source_ref']))
        result['stage'] = 'MODEL_LOADED'
        write(c['paths']['checkpoint'], dict(schema='frw.calc.inner-checkpoint.v1', operation_id=c['operation_id'],
              nonce=c['nonce'], stage='MODEL_LOADED', load_request=load_request,
              remote_endpoint=runtime['endpoint'], office_process=identity_observer(c),
              completed_operations=['RESOLVE_OWN_REMOTE_CONTEXT', 'CREATE_REMOTE_DESKTOP', 'LOAD_CALC_WORKING_COPY'],
              later_language_mutations=0))
        loaded, loaded_sha = loaded_supplier(c, pre, modules)
        need(loaded['load_request'] == load_request, 'outer_loaded_request_differs_from_actual_client')
        p = loaded['process']
        need(p['pid'] == c['office_process']['namespace_pid'] and p['start_ticks'] == c['office_process']['start_ticks']
             and p['executable_sha256'] == c['office_process']['executable_sha256'], 'loaded_Office_process_mismatch')
        # None is honest "not bound/unused" for accepted100's explicit en-US
        # configuration branch. Actual stock empty-config C.UTF-8 requires the
        # separately reviewed same-API Root delta. Never substitute en_US.UTF-8.
        need(loaded['startup_locale_environment'] is None
             or loaded['startup_locale_environment'] == {'LC_ALL': 'C.UTF-8'},
             'actual_C_UTF8_or_unbound_locale_record_required')
        need(loaded['native_transport']['mode'] == 'RAW32_POSTQUERY_NATIVE_JOIN', 'native_postjoin_mode_required')
        observe_ready()
        identity_observer(c)
        result['stage'] = 'QUALIFY_AND_QUERY'
        candidate = modules['qualifier']['qualify_and_observe'](doc, runtime['remote_context'], pre, pre_sha,
            loaded, loaded_sha, resolve_font_recipe=modules['resolver']['resolve_font_recipe'],
            measurement_leaf=modules['leaf']['observe_reference_metric'], property_value_factory=pv,
            descriptor_factory=runtime['descriptor_factory'], before_digit=phases.before, after_digit=phases.after)
        need(handler.requests == 0 and candidate.get('actual_M') is None and candidate.get('runtime_attested') is False
             and candidate['measurement']['native_font_restore_completed'] is True,
             'unreleased_restored_candidate_required')
        need(candidate['measurement']['digit_widths'] == [v['raw32'] for v in phases.responses],
             'actual_response_candidate_mismatch')
        need(doc.isReadonly() is True and doc.isModified() is False, 'readonly_unmodified_before_close_required')
        result['stage'] = 'READONLY_CLOSE'
        close_attempted = True
        doc.close(False)  # XCloseable, no ownership transfer, store/export never invoked.
        doc = None
        result['readonly_close_confirmed'] = True
        need(handler.requests == 0, 'interaction_during_close_refused')
        phases.closed()  # ONLY after full native Font restoration AND actual readonly close.
        result['stage'] = 'DESKTOP_TERMINATE'
        result['desktop_terminate_requested'] = True
        terminate_attempted = True
        need(runtime['desktop'].terminate() is True, 'remote_desktop_termination_refused')
        result.update(status='CANDIDATE_UNATTESTED_OUTER_POSTCONDITIONS_REQUIRED', stage='CLOSED',
                      candidate=candidate, responses=phases.responses)
    except Exception as exc:
        # No exception message or document/user content is emitted.
        result['error'] = dict(exception_class=type(exc).__name__, phase=result['stage'],
                               reason=str(exc) if isinstance(exc, Refused) else 'API_OR_QUALIFIER_REFUSAL')
    finally:
        if runtime is not None:
            result['handler_requests'] = runtime['handler'].requests
            if doc is not None and not close_attempted:
                try:
                    close_attempted = True
                    doc.close(False)
                    result['readonly_close_confirmed'] = True
                except Exception:
                    result['cleanup_close'] = 'UNCONFIRMED_OUTER_REQUIRED'
            elif doc is not None:
                result['cleanup_close'] = 'UNCONFIRMED_OUTER_REQUIRED'
            if result['status'] == 'REFUSED' and result['readonly_close_confirmed'] and not terminate_attempted:
                try:
                    terminate_attempted = True
                    result['desktop_terminate_requested'] = True
                    result['cleanup_terminate_return'] = runtime['desktop'].terminate() is True
                except Exception:
                    result['cleanup_terminate_return'] = 'UNCONFIRMED_OUTER_REQUIRED'
        # Deliberately no CLOSED on failed query/restoration/qualification. Outer
        # retains REFUSED and performs bounded whole-own-operation cleanup.
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inspect', action='store_true')
    p.add_argument('--input')
    p.add_argument('--input-sha256')
    p.add_argument('--output')
    a = p.parse_args(argv)
    if a.inspect or not a.input:
        print(json.dumps(dict(status='SOURCE_ONLY_SAFE_INSPECT', input_schema=SCHEMA, actual_M=None,
                              runtime_grant=False, runtime_executed=False)))
        return 0
    need(a.output is not None and safe_path(a.output).parent == Path(WORK), 'private_result_path_required')
    need(digest(a.input_sha256), 'exact_input_sha256_required')
    c = decode(protected_bytes(a.input, a.input_sha256))
    validate_config(c)
    need(a.output not in c['paths'].values(), 'distinct_result_path_required')
    result = execute_inner(c)
    atomic_json(a.output, result)
    return 0 if result['status'] == 'CANDIDATE_UNATTESTED_OUTER_POSTCONDITIONS_REQUIRED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
