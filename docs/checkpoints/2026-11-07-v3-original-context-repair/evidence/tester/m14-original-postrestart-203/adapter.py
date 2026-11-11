"""Exact original M14 singleton adaptation of full v42. Import has no live effects.

No authority issuer, observer implementation, Store, API, Runner or live checker
is constructed here. Root must supply genuine current facts before binding.
"""
import ast
import hashlib
import json
import re
import types
from pathlib import Path

BASE = Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py')
BASE_SHA = 'f0caba28ba9e823574a5149b55989aea7f4e5c893c3a89a7b4eb0ed0cf5e7ad3'
RUN_ID = 'm14-original-postrestart-query-01'
CASE = 'M-14'
OPERATION = 'M-14/OP-001'
PHASE = 'M-14-01'
SID = '20261030_093055_43bba39f'
KEY = 'agent:telegram-bot-8812646969:telegram:dm:8812646969'
REQUEST = 'После поддерживаемого рестарта тестовой площадки найди старый файл проекта «Маяк», его первоначальную версию и дополнение. Дословно процитируй пункт о хранении контрольного образца и укажи источники.'
SOURCES = [
    {'filename': 'Mayak_v1.docx', 'bytes': 39644, 'sha256': 'a9b0de026dd2959422e13e34b3f4b42190a3090471bef1d42477f88c3a4544e5'},
    {'filename': 'Mayak_addendum_v2.docx', 'bytes': 37055, 'sha256': 'e453ed5caad2ac37db9a45f96b09ea9ed4b2f42aaf3adf597259e39f6bfcde5f'},
]
EXPECTED203 = {
    'source_layers': 203, 'project_files': 487, 'native_files': 17891,
    'plugin_files': 52, 'base_source_files': 17730,
    'source_receipt_sha256': '9d8d1d954a59d5f944cb0b33c11cba3bba845cbb5d71088f335d68077c2a83c2',
    'input_sha256': '31178b28f928c937118d5c58df5aa15bb9fe23f748979cbdd9cb2f1456f513ad',
}
SCOPE = ('One genuinely missing original M-14/OP-001 phase M-14-01 controlled source/version/quote '
         'retrieval after the already completed supported native203 restart. Exact already-received '
         'Mayak original and addendum; same tester8812646969 peer8751854128 SID' + SID + '. '
         'One neutral query only; uploads0 producers0 restarts0; original300s/full180s/reserve5s; '
         'at most2 optional captured artifacts, each at most8MiB. No preference mutation, reset, '
         'old effect replay, UNKNOWN clearance or automatic followup. NOT a B00 acceptance; NOT a product acceptance. '
         'Source content and genuine persistent/session retrieval are graded externally.')
CONTRACT_FIELDS = {'schema', 'status', 'case', 'operation_id', 'phase', 'run_id',
    'scope', 'scenario_sha256', 'sources', 'expected_product', 'adapter',
    'current_gate', 'root_current_review', 'root_origin_review', 'mutable_boundary'}
MUTABLE_FIELDS = {'history_manifest_sha256', 'cursor_sha256', 'native_max_id',
    'native_boundary_sha256', 'source_origin_review_sha256', 'phase_unconsumed',
    'same_authorized_principal', 'no_old_effect_replay', 'uploads', 'producer_calls', 'restarts'}

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True) + '\n').encode()

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def sha(value):
    return type(value) is str and re.fullmatch('[a-f0-9]{64}', value) is not None

def reference(value):
    return (type(value) is dict and set(value) == {'path', 'bytes', 'sha256'}
            and type(value['path']) is str and Path(value['path']).is_absolute()
            and type(value['bytes']) is int and 0 < value['bytes'] <= 2 * 1024 * 1024
            and sha(value['sha256']))

def scenario():
    return {'tester_id': 8812646969, 'peer_id': 8751854128,
            'peer_username': '@jerichodevbot', 'deadline_seconds': 300,
            'max_updates': 65, 'pace_seconds': 1,
            'steps': [{'request': REQUEST, 'observe': {
                'mode': 'bounded_reply_capture', 'window_seconds': 180,
                'max_messages': 64, 'max_text_chars': 8000,
                'max_documents': 2, 'document_max_bytes': 8 * 1024 * 1024}}]}

SCENARIO_SHA = digest(encoded(scenario()))

def shape(name, value):
    require(name == RUN_ID and type(value) is dict and encoded(value) == encoded(scenario()),
            'only exact original M14 singleton/request/capture is permitted')
    return True

def contract_shape(contract, *, bound=True):
    require(type(contract) is dict and set(contract) == CONTRACT_FIELDS,
            'exact M14 binding fields required')
    require(contract['schema'] == 'frw.m14.exact-original.consumer-binding.v1'
            and contract['case'] == CASE and contract['operation_id'] == OPERATION
            and contract['phase'] == PHASE and contract['run_id'] == RUN_ID
            and contract['scope'] == SCOPE and contract['scenario_sha256'] == SCENARIO_SHA
            and encoded(contract['sources']) == encoded(SOURCES)
            and encoded(contract['expected_product']) == encoded(EXPECTED203),
            'exact M14 case/phase/scope/source and installed203 tuple required')
    if bound:
        require(contract['status'] == 'ROOT_BOUND_EXACT_M14', 'M14 preparation is UNBOUND; no authority')
        require(all(reference(contract[k]) for k in
                    ('adapter', 'current_gate', 'root_current_review', 'root_origin_review')),
                'Root must pin exact reviewed source and genuine current/origin evidence')
        mutable = contract['mutable_boundary']
        require(type(mutable) is dict and set(mutable) == MUTABLE_FIELDS,
                'exact current M14 mutable boundary required')
        require(all(sha(mutable[k]) for k in ('history_manifest_sha256', 'cursor_sha256',
                    'native_boundary_sha256', 'source_origin_review_sha256'))
                and mutable['source_origin_review_sha256'] == contract['root_origin_review']['sha256']
                and type(mutable['native_max_id']) is int and mutable['native_max_id'] >= 0
                and all(mutable[k] is True for k in ('phase_unconsumed',
                    'same_authorized_principal', 'no_old_effect_replay'))
                and all(type(mutable[k]) is int and mutable[k] == 0
                    for k in ('uploads', 'producer_calls', 'restarts')),
                'genuine unconsumed phase/current custody/zero producer and restart facts required')
    return True

def load_reference(ref, safe_read):
    require(reference(ref), 'exact pinned protected reference required')
    raw = safe_read(Path(ref['path']))
    require(type(raw) is bytes and len(raw) == ref['bytes'] and digest(raw) == ref['sha256'],
            'exact reviewed source/evidence bytes changed')
    return raw

def admission(contract, name, value, document):
    contract_shape(contract)
    shape(name, value)
    require(type(document) is dict and document.get('scope') == SCOPE
            and document.get('run_scenarios') == {RUN_ID: SCENARIO_SHA}
            and document.get('ordered_predecessors', {}) == {}
            and document.get('same_canonical_local_run') is False
            and 'memory_case' not in document,
            'M14 needs its own ordinary singleton authority, not M06/old predecessor authority')
    return True

def current_gate(contract, phase, state, state_raw, state_path, safe_read):
    """Actual new/send callsite. No checker is supplied or executed by preparation.

    Root's pinned check(path, sha) must reobserve actual installed bytes/process,
    fresh same-SID native quiescence, current source authorization, semantic
    all-history/once boundary, owner heads/cursor and current stop/resources.
    It must exclude only this exact pristine own run from the pinned history.
    A historical proof or old202 check() is not an implementation of this API.
    """
    contract_shape(contract)
    require(phase in ('NEW', 'CURSOR_AUTHORITY', 'PRE_INTENT_REVALIDATION'),
            'M14 current gate is only a new/pre-intent boundary, never collect or replay')
    ref = contract['current_gate']
    raw = load_reference(ref, safe_read)
    checker = types.ModuleType('root_exact_M14_current_gate')
    checker.__file__ = ref['path']
    exec(compile(raw, ref['path'], 'exec'), checker.__dict__)
    proof = contract['root_current_review']
    # Check immutable bytes ourselves as well as handing the exact pin to Root checker.
    load_reference(proof, safe_read)
    load_reference(contract['root_origin_review'], safe_read)
    facts = checker.check(proof['path'], proof['sha256'])
    require(type(facts) is dict and facts.get('admission') is False
            and facts.get('installed_product') == EXPECTED203
            and facts.get('Root_proof_sha256') == proof['sha256']
            and facts.get('m14_mutable_boundary') == contract['mutable_boundary'],
            'current actual203/source/origin/history/once/cursor tuple mismatch')
    gateway = facts.get('gateway', {})
    require(gateway.get('pid') == state['pid'] and gateway.get('start_time') == state['start_time']
            and safe_read(state_path, private=False) == state_raw,
            'gateway state changed across current native observation')
    native = facts.get('native_readonly', {})
    require(native.get('read_only') is True and native.get('quiescent') is True
            and native.get('session_id') == SID and native.get('session_key') == KEY
            and native.get('identity') == gateway,
            'fresh actual same-principal/SID native cessation required')
    return True

FOOTER = '''
# Exact M14 delta: original full receiver/locks/once/CAS/stop/budgets stay in place.
M14_CONTRACT = {contract!r}
_m14_boundary_phase = None

def _m14_adapter():
    import types as _types
    _ref = M14_CONTRACT['adapter']
    if not isinstance(_ref, dict):
        raise Refused('M14 preparation is UNBOUND; no authority')
    _raw = safe_read(Path(_ref['path']))
    if len(_raw) != _ref['bytes'] or digest(_raw) != _ref['sha256']:
        raise Refused('Exact reviewed M14 adapter changed')
    _module = _types.ModuleType('exact_M14_adapter'); _module.__file__ = _ref['path']
    exec(compile(_raw, _ref['path'], 'exec'), _module.__dict__)
    return _module

def _m14_native_freshness(state, state_raw, state_path):
    try:
        return _m14_adapter().current_gate(M14_CONTRACT, _m14_boundary_phase,
                                         state, state_raw, state_path, safe_read)
    except Exception as _exc:
        raise Refused('Exact M14 current actual/native boundary refused') from _exc

_m14_original_admission = Runner.ordinary_independent_admission
def _m14_admission(self, name, scenario):
    global _m14_boundary_phase
    try:
        _module = _m14_adapter()
        _module.contract_shape(M14_CONTRACT)
        _module.shape(name, scenario)
        _raw = safe_read(Path(self.ORDINARY_INDEPENDENT_AUTHORITY['path']))
        _candidate = json.loads(_raw, object_pairs_hook=unique_object)
        _module.admission(M14_CONTRACT, name, scenario, _candidate)
    except Exception as _exc:
        raise Refused('Exact original M14 ordinary admission refused') from _exc
    if _m14_boundary_phase is not None:
        raise Refused('Nested M14 boundary refused')
    _m14_boundary_phase = ('NEW' if getattr(self, '_m14_operation', None) == 'NEW'
                           else getattr(self, '_send_phase', None))
    try:
        _document = _m14_original_admission(self, name, scenario)
        _module.admission(M14_CONTRACT, name, scenario, _document)
        return _document
    finally:
        _m14_boundary_phase = None
Runner.ordinary_independent_admission = _m14_admission

_m14_original_new = Runner.new
def _m14_new(self, name, scenario, continuation=None):
    try:
        _module = _m14_adapter()
        _module.contract_shape(M14_CONTRACT)
        _module.shape(name, scenario)
        if continuation is not None:
            raise ValueError('M14 is a new ordinary readonly query, not a continuation')
    except Exception as _exc:
        raise Refused('Exact M14 new boundary refused') from _exc
    self._m14_operation = 'NEW'
    try:
        return _m14_original_new(self, name, scenario, continuation=None)
    finally:
        del self._m14_operation
Runner.new = _m14_new

_m14_original_send = Runner._send
def _m14_send(self, run, *, resume_prepared=False, consumer_fd=None, credential_fd=None):
    try:
        _module = _m14_adapter()
        _module.contract_shape(M14_CONTRACT)
        _module.shape(run.get('id'), run.get('scenario'))
        if (run.get('scenario_sha256') != M14_CONTRACT['scenario_sha256']
                or type(run.get('send_attempts')) is not int or run['send_attempts'] != 0
                or run.get('send_state') != 'none' or run.get('status') != 'PREPARED'
                or type(run.get('step')) is not int or run['step'] != 0
                or 'continuation_reference' in run or resume_prepared):
            raise ValueError('M14 allows one pristine ordinary attempt; no replay or prepared resume')
    except Exception as _exc:
        raise Refused('Exact M14 one-attempt boundary refused') from _exc
    return _m14_original_send(self, run, resume_prepared=False,
                              consumer_fd=consumer_fd, credential_fd=credential_fd)
Runner._send = _m14_send
'''

def successor(base_source, authority, authority_id, contract):
    """Three existing AST pins, native freshness substitution, bounded singleton footer."""
    require(digest(base_source.encode()) == BASE_SHA, 'exact complete original v42 required')
    contract_shape(contract, bound=False)
    require(type(authority) is dict and set(authority) == {'path', 'bytes', 'sha256'}
            and type(authority_id) is str and authority_id, 'exact future authority pin/id required')
    tree = ast.parse(base_source)
    runner = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Runner')
    changes = []
    for name, value in [('ORDINARY_INDEPENDENT_SCENARIOS', {RUN_ID: SCENARIO_SHA}),
                         ('ORDINARY_INDEPENDENT_AUTHORITY', authority)]:
        node = next(n for n in runner.body if isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == name for t in n.targets))
        changes.append((node.lineno, node.end_lineno, '    ' + name + ' = ' + repr(value) + '\n'))
    method = next(n for n in runner.body if isinstance(n, ast.FunctionDef)
                  and n.name == 'ordinary_independent_admission')
    matches = [n for n in ast.walk(method) if isinstance(n, ast.Constant)
               and n.value == 'ordinary-independent-jarvis-activate-20261109-r68']
    require(len(matches) == 1, 'exact original authority-id seam required')
    node = matches[0]
    lines = base_source.splitlines(keepends=True)
    line = lines[node.lineno - 1]
    changes.append((node.lineno, node.end_lineno,
                    line[:node.col_offset] + repr(authority_id) + line[node.end_col_offset:]))
    for low, high, new in sorted(changes, reverse=True):
        lines[low - 1:high] = [new]
    source = ''.join(lines)
    old = "or not 0 <= now - updated <= gateway['maximum_staleness_seconds']"
    require(source.count(old) == 1, 'exact original freshness seam required')
    source = source.replace(old, 'or not _m14_native_freshness(state, state_raw, state_path)')
    main = "if __name__ == '__main__':\n    sys.exit(main())"
    require(source.count(main) == 1, 'exact original main boundary required')
    source = source.replace(main, FOOTER.format(contract=contract) + '\n' + main)
    ast.parse(source)
    return source
