"""Original native call clocks and a sticky per-turn web launch/stop fence."""
from contextlib import contextmanager
from contextvars import ContextVar
import logging
import math
import threading
import time

_current = ContextVar('native_web_call', default=None)
_child_deadline = ContextVar('native_web_child_deadline', default=None)
_child_diagnostics = ContextVar('native_web_child_diagnostics', default=None)

# Metadata only. No exception message, response body, URL, query or traceback is
# accepted on this private lane. These records grant no retry/stop authority.
_DIAGNOSTIC_PHASES = frozenset(('keyless_exception', 'keyless_request', 'keyless_response', 'keyless_text'))
_DIAGNOSTIC_CODES = frozenset((
    'keyless tool refused', 'keyless arguments refused', 'keyless search bounds refused',
    'keyless fetch bounds refused', 'keyless URL refused', 'keyless IP URL refused',
    'keyless provider unavailable', 'keyless encoding refused', 'keyless response bound',
    'keyless timeout', 'keyless timeout refused', 'keyless envelope refused', 'keyless result refused',
    'keyless text bound', 'keyless bounded request failed',
))
_DIAGNOSTIC_EXCEPTIONS = frozenset((
    'builtins.ValueError', 'builtins.TypeError', 'builtins.KeyError',
    'builtins.AttributeError', 'builtins.OSError', 'builtins.TimeoutError',
    'builtins.RuntimeError', 'builtins.UnicodeDecodeError', 'json.decoder.JSONDecodeError',
    'requests.exceptions.RequestException', 'requests.exceptions.ConnectionError',
    'requests.exceptions.Timeout', 'requests.exceptions.ConnectTimeout',
    'requests.exceptions.ReadTimeout', 'requests.exceptions.ChunkedEncodingError',
    'requests.exceptions.ContentDecodingError', 'requests.exceptions.SSLError',
    'urllib3.exceptions.ReadTimeoutError', 'urllib3.exceptions.ProtocolError',
    'plugins.web.keyless_mcp.KeylessMCPError', 'other',
))


def begin_child_web_diagnostics():
    _child_diagnostics.set(([], threading.Lock()))


def record_child_web_diagnostic(phase, *, exception=None, code=None, http_status=None):
    state = _child_diagnostics.get()
    if state is None or phase not in _DIAGNOSTIC_PHASES:
        return
    record = {'phase': phase}
    if exception is not None:
        cls = type(exception)
        identity = cls.__module__ + '.' + cls.__name__
        record['exception'] = identity if identity in _DIAGNOSTIC_EXCEPTIONS else 'other'
    if isinstance(code, str) and code in _DIAGNOSTIC_CODES:
        record['code'] = code
    if type(http_status) is int and 100 <= http_status <= 599:
        record['http_status'] = http_status
    with state[1]:
        if len(state[0]) < 8 and record not in state[0]:
            state[0].append(record)


def child_web_diagnostics():
    state = _child_diagnostics.get()
    if state is None:
        return []
    with state[1]:
        return [dict(record) for record in state[0]]


def validate_child_web_diagnostics(records):
    if not isinstance(records, list) or len(records) > 8:
        raise RuntimeError('web_result_invalid')
    for record in records:
        if (not isinstance(record, dict) or not set(record) <= {'phase', 'exception', 'code', 'http_status'}
                or not isinstance(record.get('phase'), str) or record['phase'] not in _DIAGNOSTIC_PHASES
                or ('exception' in record and (not isinstance(record['exception'], str)
                    or record['exception'] not in _DIAGNOSTIC_EXCEPTIONS))
                or ('code' in record and (not isinstance(record['code'], str)
                    or record['code'] not in _DIAGNOSTIC_CODES))
                or ('http_status' in record and (type(record['http_status']) is not int
                    or not 100 <= record['http_status'] <= 599))):
            raise RuntimeError('web_result_invalid')
    return [dict(record) for record in records]


class WebTurn:
    def __init__(self):
        self.lock = threading.RLock()
        self.stopped = threading.Event()
        self.calls = set()
        # Trusted native failure metadata only; never reconstructed from tool text.
        self.failure = None
        self.receipt = {'status': 'QUIESCENT', 'sessions': []}

    def stop(self):
        # Admission sees the latch even while launch holds the lock. Neither a
        # reused thread id nor clear_interrupt() can clear this turn's intent.
        self.stopped.set()
        if not self.lock.acquire(timeout=2):
            self.receipt = {'status': 'STOP_UNCONFIRMED', 'reason': 'web_launch_unsettled'}
            return self.receipt
        try:
            receipts = [call.stop() for call in list(self.calls)]
            self.receipt = {'status': 'QUIESCENT' if all(r['status']=='QUIESCENT' for r in receipts)
                            else 'STOP_UNCONFIRMED', 'sessions': receipts}
            return self.receipt
        finally:
            self.lock.release()

    def fail(self, result):
        """Fence this turn's web capability and settle only owned web/browser calls."""
        if self.failure is not None:
            return dict(self.failure)
        # WebCall also carries clocks for safe file/memory operations. A web
        # failure must not turn their shared clock into a whole-turn cancel.
        self.failure = dict(result, cleanup='unknown')
        if not self.lock.acquire(timeout=2):
            receipt = {'status': 'STOP_UNCONFIRMED', 'reason': 'web_launch_unsettled'}
        else:
            try:
                receipts = [call.stop() for call in list(self.calls) if call.uses_web]
                receipt = {'status': 'QUIESCENT' if all(r['status'] == 'QUIESCENT' for r in receipts)
                           else 'STOP_UNCONFIRMED', 'sessions': receipts}
            except Exception:
                logging.getLogger(__name__).exception('Native web cleanup observation failed')
                receipt = {'status': 'STOP_UNCONFIRMED', 'reason': 'web_failure_cleanup_unobserved'}
            finally:
                self.lock.release()
        final = dict(result)
        if receipt['status'] != 'QUIESCENT':
            final['cleanup'] = 'unconfirmed'
        self.receipt = receipt
        self.failure = final
        return final


def same_web_authority(call):
    """Compare the existing retained native principal pin; never adopt a foreign call."""
    from hermes_cli.friday_user_scope import delegation_authority, ScopeDenied
    try:
        return getattr(call, 'user_authority', None) == delegation_authority()
    except ScopeDenied:
        return False


def web_retry_refused():
    """Read only this authenticated caller's native fence, never external result bytes."""
    call = _current.get()
    if call is not None and same_web_authority(call) and call.turn.failure is not None:
        return True
    from hermes_cli.friday_user_scope import _DELEGATION, delegation_visible
    delegated = _DELEGATION.get() or {}
    turn = delegated.get('web_turn')
    return (turn is not None and turn.failure is not None
            and delegation_visible(delegated.get('authority')))


class WebCall:
    def __init__(self, turn, deadline, task_id, session_id, call_id, authorization_gate=None, run_deadline=None):
        self.turn = turn
        self.base_deadline = deadline
        self.run_deadline = run_deadline
        self.authorization_gate = authorization_gate
        self.task_id, self.session_id, self.call_id = task_id, session_id, call_id
        self.turn_id = ""
        self.session_key = session_id
        self.stopped = threading.Event()
        self.session = None
        self.registry = None
        self.uses_web = False
        self.receipt = {'status': 'QUIESCENT', 'session_id': None}
        with turn.lock:
            turn.calls.add(self)

    def deadline(self):
        value = self.base_deadline
        if value is not None and self.authorization_gate is not None:
            value += self.authorization_gate.excluded_seconds()
        if self.run_deadline is not None:
            value = min(value, self.run_deadline) if value is not None else self.run_deadline
        if value is None or not math.isfinite(value):
            raise RuntimeError('web_original_deadline_required')
        return value

    def check(self):
        from tools.interrupt import is_interrupted
        if (self.stopped.is_set() or self.turn.stopped.is_set() or is_interrupted()
                or (self.uses_web and self.turn.failure is not None)):
            raise RuntimeError('web_call_stopped')
        if time.monotonic() >= self.deadline():
            raise TimeoutError('web_original_deadline')

    def stop(self):
        self.stopped.set()
        if not self.turn.lock.acquire(timeout=2):
            self.receipt = {'status':'STOP_UNCONFIRMED','reason':'web_launch_unsettled'}
            return self.receipt
        try:
            if self.session is not None:
                self.receipt = self.registry.settle_web(self.session, stop=True)
            if self.receipt['status'] == 'QUIESCENT':
                self.turn.calls.discard(self)
            return self.receipt
        finally:
            self.turn.lock.release()


def make_web_call(agent, deadline, task_id, call_id, authorization_gate=None):
    # Installed at turn start; partial callers lazily get a turn before submit.
    turn = getattr(agent, '_web_turn', None)
    if turn is None:
        delegated = getattr(agent, '_friday_delegation', None) or {}
        turn = agent._web_turn = delegated.get('web_turn') or WebTurn()
    if getattr(agent, '_interrupt_requested', False):
        turn.stopped.set()
    call = WebCall(turn, deadline, task_id, getattr(agent,'session_id','') or '', call_id,
                   authorization_gate, getattr(agent,'_web_run_deadline',None))
    call.agent = agent
    from tools.approval_context import get_current_session_key
    call.session_key = get_current_session_key(default='') or call.session_id
    call.turn_id = getattr(agent,'_current_turn_id','') or ''
    from hermes_cli.friday_user_scope import delegation_authority
    call.user_authority = delegation_authority()
    stamp = (call.session_id, call.turn_id, call.run_deadline)
    if getattr(agent, '_tool_result_call_stamp', None) != stamp:
        agent._tool_result_calls = {}
        agent._tool_result_call_stamp = stamp
    agent._tool_result_calls[(task_id, call_id)] = call
    return call


def web_call_readonly(call, agent, registry):
    """Project one original call; caller holds its turn and registry locks."""
    from copy import deepcopy
    session = call.session
    registered = getattr(agent, '_tool_result_calls', {})
    return dict(call_id=call.call_id, task_id=call.task_id,
        session_id=call.session_id, session_key=call.session_key, turn_id=call.turn_id,
        user_authority=deepcopy(call.user_authority), uses_web=call.uses_web,
        stopped=call.stopped.is_set(), turn_stopped=call.turn.stopped.is_set(),
        turn_failed=call.turn.failure is not None,
        same_active_agent=getattr(call, 'agent', None) is agent,
        same_registry_session=bool(session is not None and call.registry is registry
            and registry._running.get(session.id) is session
            and session.web_tool_call_id == call.call_id
            and session.web_turn_id == call.turn_id),
        same_web_turn=call.turn is getattr(agent, '_web_turn', None),
        registered_on_agent=registered.get((call.task_id, call.call_id)) is call)


@contextmanager
def bind_web_call(call):
    token = _current.set(call)
    try:
        yield
    finally:
        _current.reset(token)
        with call.turn.lock:
            if call.session is None:
                call.turn.calls.discard(call)


def current_web_call():
    call = _current.get()
    if call is None:
        raise RuntimeError('web_caller_context_required')
    if not same_web_authority(call):
        raise RuntimeError('web_caller_identity_mismatch')
    call.uses_web = True
    call.check()
    return call


def check_web_deadline():
    """Redispatch gate inside the trusted child, including copied asyncio contexts."""
    deadline = _child_deadline.get()
    if deadline is not None and time.monotonic() >= deadline:
        raise TimeoutError('web_original_deadline')


def child_deadline(deadline):
    if type(deadline) not in (float,int) or not math.isfinite(deadline):
        raise RuntimeError('web_original_deadline_required')
    _child_deadline.set(deadline)
    check_web_deadline()
