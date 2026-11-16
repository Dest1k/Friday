"""Private Root qualification principal at the trusted native dispatch seam.

This module is not an authenticator for arbitrary Python callers. Its sole
issuer is the genuinely owner-delegated Root executable, whose exact
RootAdmission.check performs the actual current authority checks. Constructors,
registries, projected pins and ContextVars below only retain that decision.
No ordinary user, CLI, model tool, history, DB or delegation is admitted here.
"""
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import math
import os
from pathlib import Path
import stat
import sys
import threading
import time
from types import MappingProxyType, ModuleType

from hermes_cli.friday_user_scope import ScopeDenied

KIND = 'root-qualification'
_QUALIFIER_MODULE = 'frw_root_first_qualifier'
_QUALIFIER_FILE = 'frw_root_first_qualifier.py'
_CURRENT = ContextVar('friday_private_root_qualification', default=None)
_ISSUER = object()
_ISSUED = {}
_ISSUED_LOCK = threading.RLock()


def root_context_active():
    """Pure presence guard for ordinary UserScope APIs; performs no Root IO."""
    return _CURRENT.get() is not None


class RootQualificationCleanupUnknown(RuntimeError):
    """Private retained reconciliation state; never serialize as a public reply."""

    def __init__(self, scope, original_failure=None):
        super().__init__('root_qualification_cleanup_unconfirmed')
        self.scope = scope
        self.agent = scope._agent
        self.call = scope._call
        self.admission = scope._admission
        self.original_failure = original_failure


class RootQualificationScope:
    __slots__ = ('_admission', '_admission_identity', '_operation_id', '_nonce',
                 '_entered_monotonic', '_deadline', '_work_parent',
                 '_source_binding', '_agent', '_call', '_revoked', '_closed',
                 '_guard_ceiling')

    def __init__(self, admission, issuer):
        if issuer is not _ISSUER:
            raise ScopeDenied()
        self._admission = admission
        self._admission_identity = admission._issued_identity
        self._operation_id, self._nonce = admission.operation_id, admission.nonce
        self._entered_monotonic, self._deadline = admission.entered_monotonic, admission.deadline
        self._work_parent, self._source_binding = admission.work_parent, admission.source_binding
        self._agent = self._call = None
        self._revoked = self._closed = False
        self._guard_ceiling = None

    @property
    def principal(self):
        return (KIND, self._operation_id, self._nonce)

    @property
    def entered_monotonic(self):
        return self._entered_monotonic

    @property
    def deadline(self):
        return self._deadline

    @property
    def operation_id(self):
        return self._operation_id

    @property
    def nonce(self):
        return self._nonce

    @property
    def work_parent(self):
        return self._work_parent

    @property
    def source_binding(self):
        return self._source_binding

    def _identity_unchanged(self):
        admission = self._admission
        return (admission._issued_identity is self._admission_identity
                and self._admission_identity is not None
                and admission.operation_id == self._operation_id
                and admission.nonce == self._nonce
                and admission.entered_monotonic == self._entered_monotonic
                and admission.deadline == self._deadline
                and admission.work_parent == self._work_parent
                and admission.source_binding is self._source_binding
                and getattr(admission, '_native_agent', None) is self._agent)

    def _fail(self):
        self._revoked = True
        agent = self._agent
        if agent is not None and not agent._interrupt_requested:
            # Revocation is sticky; the original turn and its custody are the
            # only stop target. No replacement call/turn is constructed.
            try:
                agent.interrupt()
            except BaseException:
                # Failed settlement is retained, never hidden by an authority
                # exception or followed by a second launch.
                agent._friday_reply_effect_unknown = True

    def check(self):
        try:
            with _ISSUED_LOCK:
                admitted = _ISSUED.get(id(self)) is self
            if (not admitted or _CURRENT.get() is not self
                    or self._revoked or self._closed or not self._identity_unchanged()):
                raise ScopeDenied()
            # The exact parent type and active issuer identity were validated
            # at dispatch. This live check remains the actual Root authority.
            expected_child_guard = min(self._deadline, self._entered_monotonic + 35) - 1
            if self._guard_ceiling not in (None, expected_child_guard):
                raise ScopeDenied()
            guard_deadline = self._deadline if self._guard_ceiling is None else self._guard_ceiling
            self._admission.check(_deadline_ceiling=guard_deadline)
            if not self._identity_unchanged():
                raise ScopeDenied()
            now = time.monotonic()
            if not self._entered_monotonic <= now < guard_deadline:
                raise ScopeDenied()
            agent = self._agent
            if (type(agent) is not NativeRootQualificationAgent
                    or agent._friday_root_qualification_scope is not self
                    or getattr(agent, '_friday_user_scope', None) is not None
                    or agent._interrupt_requested or agent._hard_interrupt_requested.is_set()
                    or agent._friday_reply_effect_unknown):
                raise ScopeDenied()
            call = self._call
            if call is not None:
                _check_registered_call(self, agent, call)
                call.check()
            return self
        except BaseException:
            self._fail()
            raise ScopeDenied() from None

    @contextmanager
    def child_execution_ceiling(self, child_deadline):
        """Bound live guard IO by the child's active time, preserving T0/Dp.

        The existing _run owns actual execution and its cleanup1. This lane
        merely prevents a current Root API check during that run from waiting
        beyond its active cutoff. No deadline or permission is renewed.
        """
        expected = min(self._deadline, self._entered_monotonic + 35)
        if (type(child_deadline) not in (int, float) or not math.isfinite(child_deadline)
                or child_deadline != expected or child_deadline - 1 <= self._entered_monotonic
                or self._guard_ceiling is not None):
            self._fail()
            raise ScopeDenied()
        self._guard_ceiling = child_deadline - 1
        try:
            self.check()
            yield
        finally:
            if (not self._revoked and not self._closed
                    and self._agent is not None and not self._agent._friday_reply_effect_unknown):
                self._guard_ceiling = None

    def _authority_pin(self):
        # Metadata after actual admission, never a bearer credential. Caller
        # obtains this only after current() has performed the live cap check.
        return {'kind': KIND, 'operation_id': self._operation_id, 'nonce': self._nonce,
                'entered_monotonic': self._entered_monotonic, 'deadline': self._deadline,
                'closure_root': str(self._source_binding['closure_root']),
                'fixedcallback_sha256': self._source_binding['fixedcallback_sha256']}


def current(required=False):
    cap = _CURRENT.get()
    if cap is None:
        if required:
            raise ScopeDenied()
        return None
    if type(cap) is not RootQualificationScope:
        raise ScopeDenied()
    return cap.check()


def retained_authority():
    return current(required=True)._authority_pin()


def _bounded_root_stop_deadline(owner, absolute_deadline):
    """Pure stop-only original Root pair/clock check, including revoked scopes.

    These retained objects were bound by the real native issuer after actual
    Root admission. They permit settlement of that owned call/turn only, never
    execution, deadline extension, fresh admission or a foreign call's stop.
    In particular this must not invoke cap.check or admission.check: expired
    and revoked operations still have an obligation to settle their custody.
    """
    from agent.web_call_context import WebCall, WebTurn
    from frw_root_qualification_entry import RootAdmission
    cap = getattr(owner, '_friday_root_qualification_scope', None)
    if (type(absolute_deadline) not in (int, float) or not math.isfinite(absolute_deadline)
            or type(cap) is not RootQualificationScope
            or type(cap._agent) is not NativeRootQualificationAgent
            or cap._agent._friday_root_qualification_scope is not cap
            or type(cap._admission) is not RootAdmission
            or cap._admission_identity is None
            or cap._agent._root_stop_binding != (cap, cap.entered_monotonic, cap.deadline)
            or not math.isfinite(cap.deadline)
            or not cap.entered_monotonic < cap.deadline <= cap.entered_monotonic + 40
            or absolute_deadline > cap.deadline
            or not ((type(owner) is WebTurn and cap._agent._web_turn is owner)
                    or (type(owner) is WebCall and cap._call is owner
                        and owner.turn is cap._agent._web_turn))):
        raise ValueError('web_root_stop_deadline_refused')
    return absolute_deadline


def _check_registered_call(cap, agent, call):
    from agent.web_call_context import WebCall, _current
    from tools.approval_context import get_current_session_key
    if (type(call) is not WebCall or _current.get() is not call
            or getattr(call, 'agent', None) is not agent
            or agent._friday_root_qualification_scope is not cap
            or call.turn is not agent._web_turn
            or call.task_id != cap.operation_id or call.call_id != cap.nonce
            or agent._tool_result_calls.get((call.task_id, call.call_id)) is not call
            or call.session_id != agent.session_id
            or call.session_key != get_current_session_key(default='')
            or call.turn_id != agent._current_turn_id
            or call.base_deadline != cap.deadline or call.run_deadline != cap.deadline
            or agent._web_run_deadline != cap.deadline
            or call.authorization_gate is not agent._root_authorization_gate
            or call.authorization_gate is None
            or call.user_authority != cap._authority_pin()
            or call.deadline() != cap.deadline
            or call.turn.failure is not None):
        raise ScopeDenied()


def check_agent(agent):
    cap = current(required=True)
    call = cap._call
    if cap._agent is not agent or call is None:
        cap._fail()
        raise ScopeDenied()
    _check_registered_call(cap, agent, call)
    return cap


class NativeRootQualificationAgent:
    """One genuinely admitted private native kind, with no model/user setup."""

    def __init__(self, cap, gate, issuer):
        if issuer is not _ISSUER:
            raise ScopeDenied()
        from agent.web_call_context import WebTurn
        self._friday_root_qualification_scope = cap
        self._friday_user_scope = None
        self._root_stop_binding = (cap, cap.entered_monotonic, cap.deadline)
        self._root_authorization_gate = gate
        self.session_id = 'root-qualification:' + cap.operation_id
        self._current_turn_id = cap.nonce
        self._web_run_deadline = cap.deadline
        self._web_turn = WebTurn()
        self._web_turn._friday_root_qualification_scope = cap
        self._tool_result_calls = {}
        self._interrupt_requested = False
        self._hard_interrupt_requested = threading.Event()
        self._friday_reply_effect_unknown = False
        self._execution_thread_id = None
        self._tool_interrupt_reason = None
        self._tool_worker_threads = set()
        self._tool_worker_threads_lock = threading.Lock()
        self._web_stop_receipt = {'status': 'QUIESCENT', 'sessions': []}

    def interrupt(self):
        from agent.friday_root_native_worker import _interrupt_worker_tids
        self._interrupt_requested = True
        self._hard_interrupt_requested.set()
        self._tool_interrupt_reason = 'root qualification revoked'
        with self._tool_worker_threads_lock:
            tids = list(self._tool_worker_threads)
        try:
            _interrupt_worker_tids(self, tids, reason=self._tool_interrupt_reason)
        finally:
            self._web_stop_receipt = self._web_turn.stop(_absolute_deadline=self._friday_root_qualification_scope.deadline)
        if self._web_stop_receipt.get('status') != 'QUIESCENT':
            self._friday_reply_effect_unknown = True
        return self._web_stop_receipt


def _fixed_callback(cap):
    """Parent loads exactly this fixed reviewed file after its Source CAS."""
    module = sys.modules.get(_QUALIFIER_MODULE)
    path = cap.source_binding['closure_root'] / _QUALIFIER_FILE
    if (type(module) is not ModuleType or Path(getattr(module, '__file__', '')) != path
            or path.resolve() != path):
        raise ScopeDenied()
    callback = getattr(module, '_qualify_current_native_call', None)
    if (not callable(callback) or getattr(callback, '__module__', None) != _QUALIFIER_MODULE
            or getattr(callback, '__globals__', None) is not module.__dict__
            or Path(getattr(getattr(callback, '__code__', None), 'co_filename', '')) != path):
        raise ScopeDenied()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid()
                or stat.S_IMODE(before.st_mode) != 0o400 or before.st_nlink != 1
                or not 0 < before.st_size <= 262144):
            raise ScopeDenied()
        data = bytearray()
        while chunk := os.read(fd, min(65536, 262145 - len(data))):
            data.extend(chunk)
            if len(data) > 262144:
                raise ScopeDenied()
        def stamp(info):
            return tuple(getattr(info, name) for name in ('st_dev', 'st_ino', 'st_uid',
                'st_gid', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))
        if (stamp(before) != stamp(os.fstat(fd)) or stamp(before) != stamp(path.lstat())
                or len(data) != before.st_size
                or hashlib.sha256(data).hexdigest() != cap.source_binding['fixedcallback_sha256']):
            raise ScopeDenied()
    finally:
        os.close(fd)
    cap.check()
    return callback


def _dispatch_root_ordinary_first_qualification(admission):
    """Trusted Root-only fixed dispatch, never a public tool/CLI/cap argument."""
    from frw_root_qualification_entry import RootAdmission
    if type(admission) is not RootAdmission:
        raise ScopeDenied()
    from hermes_cli.friday_user_scope import _CURRENT as user_current, _DELEGATION
    if root_context_active() or user_current.get() is not None or _DELEGATION.get() is not None:
        raise ScopeDenied()
    admission.check()
    if (admission._issued_identity is None or getattr(admission, '_native_agent', None) is not None
            or type(admission.operation_id) is not str
            or not admission.operation_id or type(admission.nonce) is not str or not admission.nonce
            or type(admission.entered_monotonic) not in (float, int)
            or type(admission.deadline) not in (float, int)
            or not math.isfinite(admission.entered_monotonic) or not math.isfinite(admission.deadline)
            or not admission.entered_monotonic < admission.deadline <= admission.entered_monotonic + 40
            or not isinstance(admission.work_parent, Path)
            or type(admission.source_binding) is not MappingProxyType
            or not isinstance(admission.source_binding.get('closure_root'), Path)
            or type(admission.source_binding.get('fixedcallback_sha256')) is not str
            or len(admission.source_binding['fixedcallback_sha256']) != 64
            or any(c not in '0123456789abcdef' for c in admission.source_binding['fixedcallback_sha256'])):
        raise ScopeDenied()
    from agent.friday_root_native_worker import _RootQualificationAuthorizationGate, _registered_tool_worker
    from agent.web_call_context import make_web_call, bind_web_call
    from tools.approval_context import (set_current_session_key, reset_current_session_key,
        set_current_observability_context, reset_current_observability_context)
    gate = _RootQualificationAuthorizationGate(session_key='root-qualification:' + admission.operation_id,
        lock_timeout=max(0, min(2, admission.deadline - time.monotonic())),
        _operation_id=admission.operation_id, _absolute_deadline=admission.deadline)
    cap = RootQualificationScope(admission, _ISSUER)
    agent = NativeRootQualificationAgent(cap, gate, _ISSUER)
    cap._agent = agent
    admission._native_agent = agent
    token = session_token = None
    observability = None
    call = None
    original_failure = None
    cleanup_unknown = False
    try:
        with _ISSUED_LOCK:
            _ISSUED[id(cap)] = cap
        token = _CURRENT.set(cap)
        session_token = set_current_session_key(agent.session_id)
        observability = set_current_observability_context(turn_id=agent._current_turn_id,
            tool_call_id=cap.nonce, session_id=agent.session_id)
        cap.check()
        call = make_web_call(agent, cap.deadline, cap.operation_id, cap.nonce, gate)
        cap._call = call
        call._friday_root_qualification_scope = cap
        with _registered_tool_worker(agent) as tid:
            agent._execution_thread_id = tid
            with bind_web_call(call):
                check_agent(agent)
                result = _fixed_callback(cap)()
                cap.check()
        return result
    except BaseException as exc:
        original_failure = exc
        raise
    finally:
        # A stopped/revoked capability never regains execution permission.
        cap._closed = cap._revoked = True
        try:
            if call is not None:
                receipt = call.stop(_absolute_deadline=cap.deadline)
                cleanup_unknown = receipt.get('status') != 'QUIESCENT'
            cleanup_unknown = cleanup_unknown or agent._friday_reply_effect_unknown
        except BaseException:
            cleanup_unknown = True
        finally:
            with _ISSUED_LOCK:
                _ISSUED.pop(id(cap), None)
            resets = ((reset_current_observability_context, observability),
                      (reset_current_session_key, session_token), (_CURRENT.reset, token))
            for reset, reset_token in resets:
                if reset_token is not None:
                    try:
                        reset(reset_token)
                    except BaseException:
                        cleanup_unknown = True
        if cleanup_unknown:
            agent._friday_reply_effect_unknown = True
            raise RootQualificationCleanupUnknown(cap, original_failure) from None
        if time.monotonic() >= cap.deadline:
            raise ScopeDenied() from None
