"""Operation-local ordinary Calc producer SOURCE candidate; not runtime enabled.

The concrete inner algorithm and live/terminal native joins are implemented here.
The indispensable ordinary launch/UNO4/software/font-custody construction is NOT
implemented by this package. prepare_operation refuses before launching anything.
No Root/user JSON, hash, boolean or injectable factory can bypass that refusal.
Existing exact-old observer wrappers are neither imported nor relaxed. The fixed native factory is a separate Root source package.
"""
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import time

PROFILE = 'calc-imported-native-rich-v1'
VERSION = '26.2.5.2'
COMMIT = 'cd7284b4cbbfeb507e630c1aac019f4157393acb'
RULE = 'lo-26.2.5.2-explicit-column-forward-v1'
ROLES = ('calc_document', 'calc_xlsx_filter', 'sal', 'toolkit', 'vcl')
SCALARS = dict(Hidden=True, ReadOnly=True, MacroExecutionMode=0, UpdateDocMode=0, FilterName='calc8')
CLEAN = dict(StyleName='', Width=0, CharacterWidth=0.0, Pitch=0, Slant='NONE',
             Underline=0, Strikeout=0, Orientation=0.0, Kerning=True,
             WordLineMode=False, Type=0)
_RECORD = {'index','digit','thread','font','device','string_address','raw_native',
           'outer_int32','native_return_pc','native_entry_sp','outer_entry_sp'}
_TRACE = {'schema','kind','nonce','status','records','error','exit_code','process',
          'symbols','actual_M','runtime_attested'}


class MeasuredRefused(ValueError):
    pass


class RestorationUnconfirmed(RuntimeError):
    pass


def need(condition, code):
    if not condition:
        raise MeasuredRefused(code)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True, allow_nan=False)+'\n').encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def decode(raw):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            need(key not in out, 'duplicate_internal_record_key')
            out[key] = value
        return out
    def nonfinite(_):
        raise MeasuredRefused('nonfinite_internal_record')
    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)
    except (TypeError, UnicodeError, json.JSONDecodeError):
        raise MeasuredRefused('invalid_internal_record') from None


def finite_native_family(before, source, target):
    """Called AFTER original D6 inventory, never an abbreviated input parser."""
    rich = before.rich_signature
    return (source == 'ods' and target == 'xlsx' and rich is not None
            and rich.source_kind == 'ods' and rich.native_calc_profile is True
            and getattr(before, 'destination_profile', None) == PROFILE
            and getattr(rich, '_destination_profile', None) == PROFILE)


def prepare_operation(work, data, before, *, deadline):
    """Exact missing construction cut; no placeholder native factory accepted.

    Future implementation must build the OWN ordinary _RenderCustody child with
    dynamic original source bytes, same model and launch-only native observer,
    actual UNO4/component identities and immutable font/config view. It must pass
    deadline into the child (35s) beneath _run's existing40s/original call fence.
    The retrospective systemd outer and its240s admission are inapplicable.
    """
    need(finite_native_family(before, 'ods', 'xlsx'), 'calc_measured_family_unsupported')
    need(type(data) is bytes and data and type(deadline) in (int,float)
         and math.isfinite(deadline) and time.monotonic() < deadline,
         'calc_measured_original_deadline_required')
    # Fixed trusted SOURCE dependency, never caller-selected proof/factory code.
    try:
        from hermes_cli.friday_workspace_calc_native_factory import prepare_operation as native_prepare
    except ImportError as exc:
        if exc.name != 'hermes_cli.friday_workspace_calc_native_factory':
            raise
        raise MeasuredRefused('calc_measured_native_construction_unimplemented') from None
    need(callable(native_prepare), 'calc_measured_native_prepare_unimplemented')
    operation = native_prepare(work,data,before,deadline=deadline)
    need(all(hasattr(operation,key) for key in
             ('argv','deadline','source_sha256','source_bytes','nonce')),
         'calc_measured_native_operation_fields_required')
    need(type(operation.argv) in (tuple,list) and bool(operation.argv)
         and all(type(x) is str and x for x in operation.argv)
         and operation.deadline == deadline
         and operation.source_sha256 == hashlib.sha256(data).hexdigest()
         and type(operation.source_bytes) is int and operation.source_bytes == len(data)
         and type(operation.nonce) is str and re.fullmatch('[0-9a-f]{32}',operation.nonce) is not None,
         'calc_measured_native_operation_binding_invalid')
    return operation


def _stamp(value):
    return tuple(getattr(value, field) for field in
                 ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink',
                  'st_size','st_mtime_ns','st_ctime_ns'))


def private_read(path, limit):
    """Fixed internal owned transport only, no public path parameter reaches it."""
    fd = os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
             and before.st_nlink == 1 and not before.st_mode & 0o077
             and 0 < before.st_size <= limit, 'calc_measured_private_file_required')
        chunks, size = [], 0
        while True:
            chunk = os.read(fd, min(65536,limit+1-size))
            if not chunk:
                break
            chunks.append(chunk); size += len(chunk)
            need(size <= limit, 'calc_measured_record_limit')
        after = os.fstat(fd)
        named = os.stat(path, follow_symlinks=False)
        need(_stamp(before) == _stamp(after) == _stamp(named) and size == before.st_size,
             'calc_measured_internal_file_changed')
        return b''.join(chunks)
    finally:
        os.close(fd)


def _atomic(path, value, *, exclusive=False):
    raw = canonical(value)
    need(len(raw) <= 262144, 'calc_measured_record_limit')
    path = Path(path)
    tmp = path.with_name(path.name+'.pending')
    fd = os.open(tmp, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC, 0o600)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        if exclusive:
            # link is atomic no-replace; unlink the temp ONLY after link success.
            os.link(tmp, path, follow_symlinks=False)
            os.unlink(tmp)
        else:
            os.replace(tmp,path)
    except BaseException:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise


def _check_deadline(deadline):
    need(type(deadline) in (int,float) and math.isfinite(deadline)
         and 0 < time.monotonic() < deadline, 'calc_measured_original_deadline_expired')


def _pairs(trace, *, nonce, process, symbols, responses):
    need(trace['schema'] == 'frw.native-return-trace.v1'
         and trace['kind'] == 'OFFICE_UNADMITTED', 'calc_measured_not_native_office_trace')
    need(type(trace['process']) is dict
         and set(trace['process']) == {'pid','start_ticks','gdb_pid','inferior'}
         and all(type(v) is int and v > 0 for v in trace['process'].values())
         and trace['process']['inferior'] == 1
         and type(trace['symbols']) is dict
         and set(trace['symbols']) == {'outer','native','native_return'}
         and all(type(v) is int and v > 0 for v in trace['symbols'].values()),
         'calc_measured_actual_native_identity_types_required')
    need(trace['nonce'] == nonce and trace['process'] == process and trace['symbols'] == symbols,
         'calc_measured_native_operation_mismatch')
    need(type(nonce) is str and re.fullmatch('[0-9a-f]{32}',nonce) is not None,
         'calc_measured_nonce_required')
    need(type(process) is dict and set(process) == {'pid','start_ticks','gdb_pid','inferior'}
         and all(type(v) is int and v > 0 for v in process.values()) and process['inferior'] == 1,
         'calc_measured_process_birth_required')
    need(type(symbols) is dict and set(symbols) == {'outer','native','native_return'}
         and all(type(v) is int and v > 0 for v in symbols.values()),
         'calc_measured_exact_native_symbols_required')
    need(trace['error'] is None and trace['actual_M'] is None and trace['runtime_attested'] is False,
         'calc_measured_trace_refused_or_authority_claimed')
    need(type(responses) is list and len(responses) == 10
         and all(type(x) is int and -(2**31) <= x < 2**31 for x in responses),
         'calc_measured_ten_raw32_responses_required')
    rows = trace['records']
    need(type(rows) is list and len(rows) == 10, 'calc_measured_ten_native_pairs_required')
    state = None
    for index,row in enumerate(rows):
        need(type(row) is dict and set(row) == _RECORD, 'calc_measured_native_record_schema')
        need(type(row['index']) is int and row['index'] == index and row['digit'] == str(index),
             'calc_measured_digit_order')
        need(all(type(row[k]) is int and row[k] > 0 for k in
                 ('font','device','string_address','native_return_pc','native_entry_sp','outer_entry_sp')),
             'calc_measured_native_pointer_required')
        thread = row['thread']
        need(type(thread) is list and len(thread) == 3
             and all(type(v) is int and v >= 0 for v in thread)
             and thread[0] == process['pid'] and thread[1] > 0,
             'calc_measured_native_thread_required')
        current = row['font'],row['device'],tuple(thread)
        if state is None:
            state = current
        need(current == state, 'calc_measured_reference_state_changed')
        need(row['native_return_pc'] == symbols['native_return']
             and row['native_entry_sp'] % 16 == row['outer_entry_sp'] % 16 == 8
             and row['native_entry_sp'] < row['outer_entry_sp'],
             'calc_measured_native_call_stack_mismatch')
        need(type(row['raw_native']) is int and type(row['outer_int32']) is int
             and 0 < row['raw_native'] < 65536
             and row['raw_native'] == row['outer_int32'] == responses[index],
             'calc_measured_native64_raw32_mismatch')
    return max(row['raw_native'] for row in rows)


def live_native_join(raw, *, nonce, process, symbols, responses, restored, phase, deadline):
    """LIVE-only range join. Never claims exit, cleanup, runtime admission or PASS.

    A real launcher must independently own the GDB child/process+symbol binding.
    This validator authenticates none of those values merely by comparing JSON.
    Strict old helper extensions are not consumed without their own construction.
    """
    _check_deadline(deadline)
    need(restored is True, 'calc_measured_full_Font_restore_required_before_join')
    need(type(phase) is dict and set(phase) == {'nonce','phase','index','digit'}
         and type(phase['index']) is int
         and phase == dict(nonce=nonce,phase='METRIC',index=9,digit='9'),
         'calc_measured_last_query_phase_required')
    trace = decode(raw)
    need(type(trace) is dict and set(trace) == _TRACE
         and trace['status'] == 'TEN_CALLS_OBSERVED_UNRELEASED'
         and trace['exit_code'] is None, 'calc_measured_live_trace_required')
    raw_m = _pairs(trace,nonce=nonce,process=process,symbols=symbols,responses=responses)
    return dict(raw_m=raw_m, native_records=trace['records'],
                pre_store_trace_sha256=hashlib.sha256(raw).hexdigest(),
                status='LIVE_TEN_PAIR_JOIN_ONLY_TERMINAL_UNBOUND')


def terminal_native_join(raw, *, nonce, process, symbols, responses, live):
    """Final same-operation join, separately AFTER actual store/close/owned exit."""
    trace = decode(raw)
    need(type(trace) is dict and set(trace) == _TRACE|{'own_inferior_absent'}
         and trace['status'] == 'COMPLETE_UNATTESTED'
         and type(trace['exit_code']) is int and trace['exit_code'] == 0
         and trace['own_inferior_absent'] is True, 'calc_measured_terminal_trace_required')
    raw_m = _pairs(trace,nonce=nonce,process=process,symbols=symbols,responses=responses)
    need(raw_m == live['raw_m'] and trace['records'] == live['native_records'],
         'calc_measured_terminal_changed_native_pairs')
    return dict(raw_m=raw_m,terminal_trace_sha256=hashlib.sha256(raw).hexdigest())




def _unchanged_base_projection(raw, projected, *, terminal):
    need(type(raw) is bytes and type(projected) is bytes,
         'calc_measured_verified_native_projection_required')
    original,base = decode(raw),decode(projected)
    keys = _TRACE|({'own_inferior_absent'} if terminal else set())
    need(type(original) is dict and keys <= set(original)
         and type(base) is dict and set(base) == keys
         and canonical({key:original[key] for key in keys}) == canonical(base),
         'calc_measured_native_projection_changed_base_records')


def verified_live_native_join(raw, *, work, nonce, process, symbols, source_sha256,
                              responses, restored, phase, deadline):
    """Fixed SOURCE helper custody verifier precedes the numeric live join.

    The projection is accepted only from the named controlled factory code, not
    an arbitrary callback/Root record. Its implementation verifies every required
    helper extension against actual operation state and CAS of ORIGINAL bytes.
    """
    original_sha256 = hashlib.sha256(raw).hexdigest()
    try:
        from hermes_cli.friday_workspace_calc_native_factory import verify_live_extensions
    except ImportError as exc:
        if exc.name != 'hermes_cli.friday_workspace_calc_native_factory':
            raise
        raise MeasuredRefused('calc_measured_live_native_custody_unimplemented') from None
    need(callable(verify_live_extensions), 'calc_measured_live_native_custody_unimplemented')
    projected = verify_live_extensions(raw,work=work,nonce=nonce,process=process,
        symbols=symbols,source_sha256=source_sha256,deadline=deadline)
    _unchanged_base_projection(raw,projected,terminal=False)
    joined = live_native_join(projected,nonce=nonce,process=process,symbols=symbols,
        responses=responses,restored=restored,phase=phase,deadline=deadline)
    joined['pre_store_original_trace_sha256'] = original_sha256
    return joined


def verified_terminal_native_join(raw, *, work, nonce, process, symbols, source_sha256,
                                  responses, live, deadline):
    """Factory must separately verify actual final helper/owned-tree closure."""
    original_sha256 = hashlib.sha256(raw).hexdigest()
    try:
        from hermes_cli.friday_workspace_calc_native_factory import verify_terminal_extensions
    except ImportError as exc:
        if exc.name != 'hermes_cli.friday_workspace_calc_native_factory':
            raise
        raise MeasuredRefused('calc_measured_terminal_native_custody_unimplemented') from None
    need(callable(verify_terminal_extensions), 'calc_measured_terminal_native_custody_unimplemented')
    projected = verify_terminal_extensions(raw,work=work,nonce=nonce,process=process,
        symbols=symbols,source_sha256=source_sha256,deadline=deadline)
    _unchanged_base_projection(raw,projected,terminal=True)
    joined = terminal_native_join(projected,nonce=nonce,process=process,symbols=symbols,
                                 responses=responses,live=live)
    joined['terminal_original_trace_sha256'] = original_sha256
    return joined


def _model_state(doc, input_url):
    need(doc is not None and doc.supportsService('com.sun.star.sheet.SpreadsheetDocument') is True,
         'calc_measured_real_Calc_model_required')
    need(doc.getURL() == input_url and doc.isReadonly() is True and doc.isModified() is False,
         'calc_measured_source_model_changed')
    retained = {}
    for prop in doc.getArgs():
        if prop.Name in SCALARS:
            need(prop.Name not in retained, 'calc_measured_duplicate_load_argument')
            retained[prop.Name] = prop.Value
    need(all(type(v) is type(SCALARS[k]) and v == SCALARS[k] for k,v in retained.items()),
         'calc_measured_load_argument_conflict')
    info = doc.getPropertySetInfo()
    need(info is not None and info.hasPropertyByName('ReferenceDevice'),
         'calc_measured_reference_device_unavailable')
    prop = info.getPropertyByName('ReferenceDevice')
    need(prop.Name == 'ReferenceDevice' and type(prop.Attributes) is int and prop.Attributes & 16
         and prop.Type.typeName == 'com.sun.star.awt.XDevice',
         'calc_measured_reference_device_contract_changed')
    device = doc.getPropertyValue('ReferenceDevice')
    need(device is not None and all(callable(getattr(device,k,None)) for k in ('createGraphics','getFont')),
         'calc_measured_reference_device_unavailable')
    return device,dict(url=input_url,readonly=True,modified=False,retained_load_arguments=retained)


def _font(doc, remote_context, pv, runtime):
    # Exact unchanged reviewed resolver body, no substitute locale/font guessing.
    from hermes_cli.friday_workspace_calc_font_resolver import resolve_font_recipe
    return resolve_font_recipe(doc,remote_context,property_value_factory=pv,
        startup_locale_environment=runtime['startup_locale_environment'],
        stock_startup_locale_lifecycle=runtime['stock_startup_locale_lifecycle'])


def _measure(doc, device, font, pv_descriptor, *, work, nonce, deadline):
    descriptor_values = dict(CLEAN,**font['recipe'])
    descriptor = pv_descriptor(descriptor_values)
    need(all((getattr(descriptor,k).value if k == 'Slant' else getattr(descriptor,k)) == v
             for k,v in descriptor_values.items()), 'calc_measured_export_descriptor_changed')
    restore = device.createGraphics()  # captures COMPLETE native Font, held through finally
    need(restore is not None, 'calc_measured_full_Font_restore_capability_required')
    responses = []
    try:
        seed = device.createGraphics()
        need(seed is not None, 'calc_measured_clean_Font_seed_required')
        seed.selectFont(descriptor)
        seed.getFontMetric()  # installs clean vcl::Font, no draw
        reference_font = device.getFont(descriptor)
        need(reference_font is not None, 'calc_measured_reference_font_missing')
        for index,digit in enumerate('0123456789'):
            _check_deadline(deadline)
            phase = dict(nonce=nonce,phase='METRIC',index=index,digit=digit)
            _atomic(work/'phase.json',phase)
            value = reference_font.getStringWidth(digit)
            need(type(value) is int and -(2**31) <= value < 2**31,
                 'calc_measured_raw32_response_required')
            need(decode(private_read(work/'phase.json',4096)) == phase,
                 'calc_measured_query_phase_changed')
            responses.append(value)
    finally:
        try:
            restore.getFontMetric()  # exact full old Font, no descriptor approximation
        except Exception as exc:
            raise RestorationUnconfirmed('calc_measured_full_Font_restore_unconfirmed') from exc
    return responses,descriptor_values


def produce_on_remote(runtime, *, work, source_sha256, source_bytes, nonce, process, symbols, deadline):
    """Concrete inner load→measure→restore→live join→one store→close algorithm.

    Runtime MUST come from the as-yet-missing sole owned native constructor;
    this function is not a public proof loader or native launch/custody authority.
    It performs no second load/render and never stores on failed restoration/join.
    """
    work = Path(work)
    input_path, output_path = work/'input.ods',work/'out/input.xlsx'
    input_url = input_path.as_uri()
    need(_sha(source_sha256) and type(source_bytes) is int and source_bytes > 0,
         'calc_measured_dynamic_source_binding_required')
    source_raw = private_read(input_path,1000000)
    need(len(source_raw) == source_bytes and hashlib.sha256(source_raw).hexdigest() == source_sha256,
         'calc_measured_dynamic_source_mismatch')
    need(not os.path.lexists(output_path), 'calc_measured_output_already_exists')
    _check_deadline(deadline)
    # Both actual held-stop/font-view boundaries are indispensable when the
    # reviewed native helper path is used; no no-helper success is substituted.
    try:
        from hermes_cli.friday_workspace_calc_native_factory import loaded_model_barrier, readonly_closed_barrier
    except ImportError as exc:
        if exc.name != 'hermes_cli.friday_workspace_calc_native_factory':
            raise
        raise MeasuredRefused('calc_measured_native_boundaries_unimplemented') from None
    need(callable(loaded_model_barrier) and callable(readonly_closed_barrier),
         'calc_measured_native_boundaries_unimplemented')
    need(type(runtime) is dict and
         {'desktop','handler','property_value_factory','descriptor_factory','remote_context',
          'local_context','startup_locale_environment','stock_startup_locale_lifecycle'} <= set(runtime),
         'calc_measured_controlled_runtime_fields_required')
    desktop,handler,pv = runtime['desktop'],runtime['handler'],runtime['property_value_factory']
    need(type(getattr(handler,'requests',None)) is int and handler.requests == 0
         and callable(pv) and callable(runtime['descriptor_factory']),
         'calc_measured_controlled_runtime_contract_required')
    need(runtime['remote_context'] is not runtime['local_context'], 'calc_measured_remote_context_required')
    args = tuple(pv(k,v) for k,v in SCALARS.items())+(pv('InteractionHandler',handler),)
    doc = None
    close_attempted = False
    try:
        doc = desktop.loadComponentFromURL(input_url,'_blank',0,args)
        need(doc is not None and handler.requests == 0, 'calc_measured_load_or_interaction_refused')
        device,before = _model_state(doc,input_url)
        loaded_model_barrier(runtime,doc,work=work,nonce=nonce,process=process,symbols=symbols,
            source_sha256=source_sha256,source_bytes=source_bytes,deadline=deadline)
        _check_deadline(deadline)
        font_before = _font(doc,runtime['remote_context'],pv,runtime)
        need(font_before['default_script']['value'] == 'LATIN' and font_before['use_printer_metrics'] is False,
             'calc_measured_reference_profile_unsupported')
        responses,descriptor = _measure(doc,device,font_before,runtime['descriptor_factory'],
                                        work=work,nonce=nonce,deadline=deadline)
        _,after = _model_state(doc,input_url)
        font_after = _font(doc,runtime['remote_context'],pv,runtime)
        need(before == after and font_before == font_after and handler.requests == 0,
             'calc_measured_font_model_or_config_drift')
        # Snapshot remains UNRELEASED; terminal validation is a different stage.
        live = verified_live_native_join(private_read(work/'native-trace.json',262144),
            work=work,nonce=nonce,source_sha256=source_sha256,
            process=process,symbols=symbols,responses=responses,restored=True,
            phase=decode(private_read(work/'phase.json',4096)),deadline=deadline)
        _,before_store = _model_state(doc,input_url)
        font_before_store = _font(doc,runtime['remote_context'],pv,runtime)
        need(before_store == before and font_before_store == font_before
             and handler.requests == 0, 'calc_measured_postjoin_state_drift')
        need(private_read(input_path,1000000) == source_raw, 'calc_measured_source_changed_before_store')
        _check_deadline(deadline)
        # Exactly ONE stock storeToURL on THIS readonly source model. No retry.
        doc.storeToURL(output_path.as_uri(),tuple(pv(k,v) for k,v in
            [('FilterName','Calc MS Excel 2007 XML'),('Overwrite',True),
             ('ConversionRequestOrigin','CommandLine'),('InteractionHandler',handler)]))
        need(handler.requests == 0, 'calc_measured_interaction_during_store_refused')
        _,post_store = _model_state(doc,input_url)
        font_post_store = _font(doc,runtime['remote_context'],pv,runtime)
        need(post_store == before and font_post_store == font_before,
             'calc_measured_state_changed_around_store')
        _check_deadline(deadline)
        need(private_read(input_path,1000000) == source_raw, 'calc_measured_source_changed_after_store')
        # Successful close is distinct from native/helper/process terminal proof.
        close_attempted = True
        doc.close(False)
        doc = None
        need(handler.requests == 0, 'calc_measured_interaction_during_close_refused')
        _atomic(work/'phase.json',dict(nonce=nonce,phase='CLOSED',index=None,digit=None))
        readonly_closed_barrier(work=work,nonce=nonce,process=process,symbols=symbols,
            source_sha256=source_sha256,deadline=deadline)
        _check_deadline(deadline)
        need(desktop.terminate() is True, 'calc_measured_desktop_termination_refused')
        return dict(schema='frw.ordinary-calc.inner-one-store-candidate.v1',nonce=nonce,
                    source_sha256=source_sha256,source_bytes=source_bytes,
                    responses=responses,live=live,font=font_before,descriptor=descriptor,
                    source_state=before,readonly_close_confirmed=True,store_count=1,
                    handler_requests=0,process=process,symbols=symbols,
                    actual_M=None,runtime_attested=False,terminal='UNBOUND_PARENT')
    finally:
        if doc is not None and not close_attempted:
            # No saving/second-store on failure. Launcher still MUST terminate/reap.
            doc.close(False)


def read_verified_operation(work, operation, source, output):
    """NO JSON authority implementation is supplied in place of missing custody.

    Required final implementation consumes producer/native/controller terminal
    observations only after _run reaped the OWN namespace; recomputes bytes here;
    verifies the exact trusted constructed font/software/stock/no-injection view;
    and returns internal facts. Matching record hashes alone cannot do that.
    """
    try:
        from hermes_cli.friday_workspace_calc_native_factory import verify_terminal
    except ImportError as exc:
        if exc.name != 'hermes_cli.friday_workspace_calc_native_factory':
            raise
        raise MeasuredRefused('calc_measured_native_terminal_custody_unimplemented') from None
    need(type(source) is bytes and type(output) is bytes and source and output,
         'calc_measured_parent_original_bytes_required')
    need(callable(verify_terminal), 'calc_measured_native_terminal_custody_unimplemented')
    facts = verify_terminal(work,operation,source,output)
    _verified_fact_shape(facts)
    return facts


def _verified_fact_shape(facts):
    """Shape/domain checks only; native construction is the SOURCE authority."""
    digests = ('recipe_sha256','font_descriptor_sha256','font_view_sha256',
               'reference_state_sha256','applicability_sha256')
    required = set(digests)|{'producer_version','reviewed_source_commit','numeric_rule',
        'component_sha256','source_style_name','source_font','default_script','export_name',
        'export_charset','raw_font_height','raw_m'}
    need(type(facts) is dict and set(facts) == required,
         'calc_measured_verified_fact_fields_required')
    need(all(_sha(facts[k]) for k in digests), 'calc_measured_verified_fact_digest_invalid')
    need(facts['producer_version'] == VERSION and facts['reviewed_source_commit'] == COMMIT
         and facts['numeric_rule'] == RULE, 'calc_measured_verified_producer_unsupported')
    rows = facts['component_sha256']
    need(type(rows) is tuple and len(rows) == len(ROLES)
         and all(type(row) is tuple and len(row) == 2 for row in rows)
         and tuple(row[0] for row in rows) == ROLES and all(_sha(row[1]) for row in rows),
         'calc_measured_verified_components_invalid')
    need(facts['source_style_name'] == 'Default' and facts['default_script'] == 'LATIN'
         and type(facts['source_font']) is tuple and len(facts['source_font']) == 2
         and facts['source_font'][0] == 'Calibri' and type(facts['source_font'][1]) is Decimal
         and facts['source_font'][1].is_finite() and facts['source_font'][1] == Decimal(11)
         and type(facts['raw_font_height']) is int and facts['raw_font_height'] == 220,
         'calc_measured_verified_font_unsupported')
    need(type(facts['export_name']) is str and 0 < len(facts['export_name']) <= 128
         and not any(ord(c) < 32 for c in facts['export_name'])
         and type(facts['export_charset']) is int and facts['export_charset'] in (0,1)
         and type(facts['raw_m']) is int and 0 < facts['raw_m'] < 65536,
         'calc_measured_verified_reference_unsupported')
