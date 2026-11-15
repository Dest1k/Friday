"""Finite pure adapter checks: no GDB, inferior, subprocess or policy effects."""
from pathlib import Path
from types import SimpleNamespace
import ast
import hashlib
import json
import resource
import signal

resource.setrlimit(resource.RLIMIT_CPU, (8, 10))
signal.alarm(15)
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'candidate/paper_helper_gdb.py'
raw = SOURCE.read_bytes()
ns = {'__name__': 'pure_candidate', '__file__': str(SOURCE)}
exec(compile(raw, str(SOURCE), 'exec'), ns)
Adapter = ns['Adapter']
results = []


class BP:
    def __init__(self, number=-83, delete_error=False):
        self._number = number
        self._valid = True
        self._enabled = True
        self._inferior = 2
        self.deleted = 0
        self.delete_error = delete_error

    def _checked(self, value):
        if not self._valid:
            raise RuntimeError('invalidated_object_property_read')
        return value

    @property
    def number(self):
        return self._checked(self._number)

    @property
    def enabled(self):
        return self._checked(self._enabled)

    @property
    def inferior(self):
        return self._checked(self._inferior)

    def is_valid(self):
        return self._valid

    def delete(self):
        if self.delete_error:
            raise RuntimeError('test_delete_refused')
        self.deleted += 1
        self._valid = False


def fixture(*, one_shot=True, field=None, handler_error=False, delete_error=False):
    bp = BP(delete_error=delete_error)
    a = Adapter.__new__(Adapter)
    state = {'error': None}
    calls = []
    publishes = []

    def fail(reason):
        if state['error'] is None:
            state['error'] = reason

    def handler():
        calls.append('handler')
        if handler_error:
            raise RuntimeError('test_handler_refused')

    expected = (2, 42, (42, 7, 0), 0x1000)
    actual = list(expected)
    if field is not None:
        actual[field] = (42, 8, 0) if field == 2 else actual[field] + 1
    a.g = SimpleNamespace(selected_inferior=lambda: SimpleNamespace(num=actual[0], pid=actual[1]),
                          newest_frame=lambda: SimpleNamespace(pc=lambda: actual[3]))
    a.tid = lambda: actual[2]
    a.n = {'STATE': state, 'fail': fail}
    a.pending_stop = (bp, handler, one_shot, *expected)
    a.pending = None
    a.to_create = []
    a.breakpoints = [bp]
    a.stop_handlers = {-83: (bp, handler, one_shot)}
    a.retired_breakpoints = set()
    a.publish = lambda: publishes.append('publish')
    return a, bp, state, calls, publishes


def check(name, fn):
    fn()
    results.append({'name': name, 'status': 'PASS'})


def accepted_one_shot():
    a, bp, state, calls, pubs = fixture()
    assert a.dispatch() == 'CONTINUE'
    assert calls == ['handler'] and pubs == ['publish'] and state['error'] is None
    assert bp.deleted == 1 and not bp.is_valid()
    assert not a.breakpoints and not a.stop_handlers and a.retired_breakpoints == {-83}
    assert a.dispatch() is None and bp.deleted == 1


def persistent_popen():
    a, bp, state, calls, pubs = fixture(one_shot=False)
    assert a.dispatch() == 'CONTINUE'
    assert calls == ['handler'] and pubs == ['publish'] and state['error'] is None
    assert bp.is_valid() and bp.enabled and bp.deleted == 0
    assert a.breakpoints == [bp] and -83 in a.stop_handlers and not a.retired_breakpoints


def invalid_context(field):
    a, bp, state, calls, pubs = fixture(field=field)
    assert a.dispatch() is None
    assert state['error'] == 'helper_stop_event_context_changed'
    assert not calls and not pubs and bp.deleted == 0 and bp.is_valid()
    assert a.breakpoints == [bp] and -83 in a.stop_handlers and not a.retired_breakpoints


def handler_refusal():
    a, bp, state, calls, pubs = fixture(handler_error=True)
    assert a.dispatch() is None and state['error'] == 'test_handler_refused'
    assert calls == ['handler'] and not pubs and bp.deleted == 0 and bp.is_valid()
    assert -83 in a.stop_handlers and not a.retired_breakpoints


def delete_refusal():
    a, bp, state, calls, pubs = fixture(delete_error=True)
    assert a.dispatch() is None and state['error'] == 'test_delete_refused'
    assert calls == ['handler'] and not pubs and bp.deleted == 0 and bp.is_valid()
    assert -83 in a.stop_handlers and not a.retired_breakpoints


def first_error_terminal():
    a, bp, state, calls, pubs = fixture()
    state['error'] = 'original_refusal'
    a.to_create = [(0x2000, lambda: None)]
    a.pending = 'CONTINUE'
    assert a.dispatch() is None and state['error'] == 'original_refusal'
    assert a.pending_stop is None and not a.to_create and a.pending is None
    assert not calls and not pubs and bp.deleted == 0
    assert a.queue_stop(SimpleNamespace(breakpoints=[bp])) is True
    assert state['error'] == 'original_refusal' and a.pending_stop is None


def retired_delivery_refused():
    a, bp, state, calls, pubs = fixture()
    assert a.dispatch() == 'CONTINUE'
    event = SimpleNamespace(breakpoints=[SimpleNamespace(number=-83)])
    try:
        a.queue_stop(event)
    except RuntimeError as exc:
        assert str(exc) == 'helper_retired_breakpoint_event'
    else:
        raise AssertionError('retired_delivery_accepted')
    assert calls == ['handler'] and pubs == ['publish'] and bp.deleted == 1
    assert a.pending_stop is None


def invalidated_delivery_refused():
    a, bp, state, calls, pubs = fixture()
    assert a.dispatch() == 'CONTINUE'
    try:
        a.queue_stop(SimpleNamespace(breakpoints=[bp]))
    except RuntimeError as exc:
        assert str(exc) == 'invalidated_object_property_read'
    else:
        raise AssertionError('invalidated_delivery_accepted')
    assert calls == ['handler'] and bp.deleted == 1 and a.pending_stop is None


def duplicate_delivery_refused():
    a, bp, state, calls, pubs = fixture()
    a.pending_stop = None
    try:
        a.queue_stop(SimpleNamespace(breakpoints=[bp, bp]))
    except RuntimeError as exc:
        assert str(exc) == 'helper_ambiguous_or_duplicate_stop_event'
    else:
        raise AssertionError('duplicate_delivery_accepted')
    assert not calls and not pubs and bp.deleted == 0 and a.pending_stop is None


def unknown_delivery_unclaimed():
    a, bp, state, calls, pubs = fixture()
    a.pending_stop = None
    assert a.queue_stop(SimpleNamespace(breakpoints=[SimpleNamespace(number=777)])) is False
    assert not calls and not pubs and bp.deleted == 0 and a.pending_stop is None


def invalid_breakpoint_refused():
    a, bp, state, calls, pubs = fixture()
    bp._enabled = False
    assert a.dispatch() is None and state['error'] == 'helper_stop_breakpoint_changed'
    assert not calls and not pubs and bp.deleted == 0 and bp.is_valid()


def stop_predicate_unchanged():
    tree = ast.parse(raw)
    predicates = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == 'ObserverBreakpoint']
    assert len(predicates) == 1
    methods = [n for n in predicates[0].body if isinstance(n, ast.FunctionDef) and n.name == 'stop']
    assert len(methods) == 1 and len(methods[0].body) == 1
    assert isinstance(methods[0].body[0], ast.Return) and methods[0].body[0].value.value is True


check('accepted_one_shot_destroyed_without_invalidated_property_reads', accepted_one_shot)
check('persistent_popen_entry_retained', persistent_popen)
for field, name in enumerate(['inferior', 'pid', 'ptid', 'pc']):
    check('changed_' + name + '_refuses_before_handler_or_delete', lambda field=field: invalid_context(field))
check('handler_refusal_keeps_breakpoint_and_no_publish', handler_refusal)
check('delete_failure_fails_closed_before_resume', delete_refusal)
check('first_error_is_terminal_and_preserved', first_error_terminal)
check('readable_retired_event_is_explicitly_refused', retired_delivery_refused)
check('invalidated_event_is_refused_without_advancement', invalidated_delivery_refused)
check('ambiguous_duplicate_event_is_refused', duplicate_delivery_refused)
check('foreign_event_is_unclaimed_without_advancement', unknown_delivery_unclaimed)
check('disabled_breakpoint_is_refused_before_handler', invalid_breakpoint_refused)
check('stop_predicate_stays_pure', stop_predicate_unchanged)
result = {'schema': 'frw.calc.gdb-one-shot-pure-checks.v1',
          'candidate_sha256': hashlib.sha256(raw).hexdigest(),
          'scope': 'Pure fake GDB objects; no native GDB or inferior execution. Not runtime qualification.',
          'checks': results, 'passed': len(results), 'status': 'PASS'}
p = ROOT / 'PURE-CHECKS.json'
p.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
p.chmod(0o600)
print(json.dumps({'status': result['status'], 'passed': len(results), 'candidate_sha256': result['candidate_sha256']}))
