"""Pure metadata validator. It does not launch, query, attest runtime, or compute M.
Expected trace hash and custody facts MUST come from trusted Root, not the trace.
A fixture is permanently ineligible to provide Office native-range evidence.
"""
import hashlib
import json


class Unbound(ValueError):
    pass


def require(value, reason):
    if not value:
        raise Unbound(reason)


def integer(value):
    return type(value) is int


def validate_trace(raw_bytes, *, expected_sha256, nonce, process, symbols, uno_widths,
                   root_custody_confirmed, load_dependency=None, validate_dependency=None,
                   gpgme_engine_init=None, validate_gpgme_engine_init=None):
    require(type(raw_bytes) is bytes and hashlib.sha256(raw_bytes).hexdigest() == expected_sha256,
            'trace_bytes_changed')
    require(root_custody_confirmed is True, 'Root_custody_UNBOUND')
    t = json.loads(raw_bytes)
    keys = {'schema','kind','nonce','status','records','error','exit_code','process',
            'symbols','actual_M','runtime_attested','own_inferior_absent'}
    expected_keys = keys | ({'load_dependency'} if load_dependency is not None else set())
    expected_keys |= {'gpgme_engine_init'} if gpgme_engine_init is not None else set()
    require(set(t) == expected_keys, 'trace_schema')
    if load_dependency is not None:
        require(callable(validate_dependency), 'trusted_helper_validator_required')
        validate_dependency(t['load_dependency'], load_dependency, process)
    if gpgme_engine_init is not None:
        require(load_dependency is not None and callable(validate_gpgme_engine_init),
                'trusted_separate_gpgme_validator_required')
        validate_gpgme_engine_init(t['gpgme_engine_init'], gpgme_engine_init, process)
    require(t['schema'] == 'frw.native-return-trace.v1' and t['kind'] == 'OFFICE_UNADMITTED'
            and t['status'] == 'COMPLETE_UNATTESTED', 'not_complete_Office_native_evidence')
    require(t['nonce'] == nonce and t['process'] == process and t['symbols'] == symbols,
            'Root_process_phase_symbol_binding_changed')
    require(t['error'] is None and type(t['exit_code']) is int and t['exit_code'] == 0
            and t['own_inferior_absent'] is True and t['actual_M'] is None
            and t['runtime_attested'] is False, 'exit_cleanup_or_authority_UNBOUND')
    require(type(t['process']) is dict and all(integer(v) for v in t['process'].values())
            and type(t['symbols']) is dict and all(integer(v) for v in t['symbols'].values()),
            'trace_identity_integer_types')
    require(type(process) is dict and set(process) == {'pid','start_ticks','gdb_pid','inferior'}
            and all(integer(v) and v > 0 for v in process.values()) and process['inferior'] == 1,
            'process_identity')
    require(type(symbols) is dict and set(symbols) == {'outer','native','native_return'}
            and all(integer(v) and v > 0 for v in symbols.values()), 'symbol_identity')
    require(type(uno_widths) is list and len(uno_widths) == 10
            and all(integer(v) for v in uno_widths), 'ten_external_UNO_widths_required')
    require(type(t['records']) is list and len(t['records']) == 10, 'ten_calls_required')
    device = font = thread = None
    for index, r in enumerate(t['records']):
        require(type(r) is dict and set(r) == {'index','digit','thread','font','device','string_address',
                'raw_native','outer_int32','native_return_pc','native_entry_sp','outer_entry_sp'}, 'record_schema')
        require(integer(r['index']) and r['index'] == index and r['digit'] == str(index), 'digit_sequence')
        require(all(integer(r[k]) and r[k] > 0 for k in ('font','device','string_address',
                    'native_return_pc','native_entry_sp','outer_entry_sp')), 'pointer_or_stack_unknown')
        require(type(r['thread']) is list and len(r['thread']) == 3
                and all(integer(v) and v >= 0 for v in r['thread'])
                and r['thread'][0] == process['pid'] and r['thread'][1] > 0, 'thread_identity')
        if index == 0:
            device, font, thread = r['device'], r['font'], r['thread']
        require((r['device'],r['font'],r['thread']) == (device,font,thread), 'state_binding_changed')
        require(r['native_return_pc'] == symbols['native_return']
                and r['native_entry_sp'] % 16 == 8 and r['outer_entry_sp'] % 16 == 8
                and r['native_entry_sp'] < r['outer_entry_sp'], 'caller_stack_binding')
        require(integer(r['raw_native']) and integer(r['outer_int32'])
                and 0 < r['raw_native'] < 65536 and r['raw_native'] == r['outer_int32'] == uno_widths[index],
                'native_range_or_UNO_mismatch')
    return {'schema':'frw.native-range-evidence.v1', 'status':'NATIVE_BOUND_EVIDENCE_ONLY',
            'trace_sha256':expected_sha256, 'nonce':nonce, 'process':process, 'symbols':symbols,
            'thread':thread,'font':font,'device':device, 'native_width_supported_range':True,
            'ten_native_equals_outer_equals_UNO':True, 'actual_M':None,'runtime_attested':False,
            'scope':'Only these ten calls; Root owns font/device qualification, restore, close, source hash and all process-tree cleanup.'}
