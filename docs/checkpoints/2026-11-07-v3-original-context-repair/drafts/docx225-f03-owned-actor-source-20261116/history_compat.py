"""Pure Source adapter; exact old F03 readonly custody, never admission/effects."""
import ast
import hashlib

METHOD_PINS = {
 'send_ack_budget':'e98ccec199a6402f6d2fef062a8ac3b10aadfa32addf53017c11fd7ef43c9df2',
 'load':'c7303daacef29637946baf05d80110dc48974c5ea50f36219744db58c47a0143',
 'valid_send_budget':'e33dbccc161b7805b2c23d5e46ba721aa3d95e2be72da59a19a7447a89ea5791',
 'reply_window':'35ba489b735b58beb429a6128cb81482f2ca8122ccb3aa06bd7496e881acb59d',
 'verify_window':'7632477e0bd593fbb0c2c0db188eed2b4cdd82a3b06aa09d8c2308b516f3c5f9',
 'verify_reply_custody':'aaaa833871b1b7ecf2f2e16cf8c04d6a50a0504d5740d3f5d02ed43541d318f7',
 'receive_context':'9168b3a58fde7d0da35ec1ca79ea16b90b1b0732fa44ef22452ea6793287ef9d',
 'receive_inventory':'f83047e3bb68d4907a0ee8f17aaefb7deba8b1ae705914162fab560e82427740',
 'verify_capture_context':'fd1edfe7bc09470b52aceb01617c3c562878a837f465f6167b3afa9b1fa2b30f',
}

SEAM = r'''
# Exact already-consumed historical F03 receive/window/ACK compatibility.
# guard, _send, send, API, clocks and original run bytes remain unchanged.
_F03_HISTORY_RUN = 'f03-ods-formulas-original-221-20261114'
_F03_HISTORY_RUN_BYTES = 19759
_F03_HISTORY_RUN_SHA = 'dafed4bc762b17feb565f3b2efaa5d8e454060ba3576dfeb9d90159a3f67cdc9'
_F03_HISTORY_STATE = Path('/home/jericho/.local/share/friday-telegram-bot-test')
_F03_HISTORY_SOURCE = {
    'path': '/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114/separate-missing-first-send-phase/bot_tester.f03.first-send.bound.py',
    'bytes': 1148096,
    'sha256': 'b901b7ac63e4ff0a6e279d2e13651ec03fb6d7de93866ae3cdf1b8d7ca85e9e1',
}
_F03_HISTORY_MODULE = None
_F03_HISTORY_READ_METHODS = ('receive_context', 'receive_inventory',
    'valid_send_budget', 'reply_window', 'verify_window', 'verify_capture_context',
    'verify_reply_custody', 'send_ack_budget', 'load')


def _f03_history_select(run):
    if not isinstance(run, dict):
        return False
    selected = run.get('id') == _F03_HISTORY_RUN
    if 'first_send_phase' in run and not selected:
        raise Refused('Unknown historical first-send schema/owner; no compatibility grant')
    return selected


def _f03_history_exact(self, run):
    if (self.store.root != _F03_HISTORY_STATE
            or not isinstance(run, dict) or run.get('id') != _F03_HISTORY_RUN):
        raise Refused('Exact historical F03 owner/state required')
    raw = safe_read(self.store.run_path(_F03_HISTORY_RUN))
    if (len(raw) != _F03_HISTORY_RUN_BYTES or digest(raw) != _F03_HISTORY_RUN_SHA
            or encoded(run) != raw
            or run.get('status') != 'EVIDENCE_READY' or run.get('send_state') != 'sent'
            or run.get('send_attempts') != 1 or 'first_send_phase' not in run):
        raise Refused('Historical F03 row changed; replay and clock replacement refused')


def _f03_history_source_module():
    global _F03_HISTORY_MODULE
    ref = _F03_HISTORY_SOURCE
    raw = safe_read(Path(ref['path']), ref['bytes'])
    if len(raw) != ref['bytes'] or digest(raw) != ref['sha256']:
        raise Refused('Authentic historical F03 producer changed')
    if _F03_HISTORY_MODULE is None:
        import types as _history_types
        module = _history_types.ModuleType('_frw_exact_f03_history_producer')
        module.__file__ = ref['path']
        exec(compile(raw, ref['path'], 'exec'), module.__dict__)
        _F03_HISTORY_MODULE = module
    return _F03_HISTORY_MODULE


class _F03HistoryReadStore:
    """Existing reader surface, without initializing a store or exposing writes."""
    def __init__(self, source):
        self.root = source.root
        self.runs = source.runs
        self.captures = source.captures
        self.downloads = source.downloads
        self.run_path = source.run_path
        self.get = source.get


def _f03_history_no_effect(*args, **kwargs):
    raise Refused('Historical F03 delegation is readonly; no effect allowed')


def _f03_history_call(self, method, run, *args, **kwargs):
    if method not in _F03_HISTORY_READ_METHODS:
        raise Refused('Historical F03 method is not a readonly entry')
    _f03_history_exact(self, run)
    module = _f03_history_source_module()
    # Authentic initializer only sets local attributes; no historical execution
    # method is exposed. Store is a reader, API absent, clock stays the caller's.
    view = module.Runner(_F03HistoryReadStore(self.store), None,
                         clock=self.clock, sleep=_f03_history_no_effect)
    # Preserve current complete global inventory, including subsequent rows.
    # Its calls to the authentic inventory carry an explicit checked cursor.
    view.cursor_offsets = self.cursor_offsets
    for effect in ('guard', 'send', '_send', 'save', 'capture', 'capture_reply',
                   'process', 'commit_receive', 'keep_ack', 'terminal_drain',
                   'poll_updates', 'observe', 'prepared_first_send'):
        setattr(view, effect, _f03_history_no_effect)
    try:
        argument = _F03_HISTORY_RUN if method == 'load' else run
        result = getattr(view, method)(argument, *args, **kwargs)
    except Exception as exc:
        raise Refused('Exact historical F03 readonly ' + method + ' refused') from exc
    _f03_history_exact(self, run)
    return result


def _f03_history_wrap(name):
    original = getattr(Runner, name)
    def readonly(self, run, *args, **kwargs):
        if _f03_history_select(run):
            return _f03_history_call(self, name, run, *args, **kwargs)
        return original(self, run, *args, **kwargs)
    return readonly


for _f03_history_method in (
        'receive_context', 'receive_inventory', 'valid_send_budget',
        'reply_window', 'verify_window', 'verify_capture_context',
        'verify_reply_custody', 'send_ack_budget'):
    setattr(Runner, _f03_history_method, _f03_history_wrap(_f03_history_method))

_f03_history_original_load = Runner.load

def _f03_history_load(self, name):
    if name == _F03_HISTORY_RUN:
        run = self.store.get(self.store.run_path(name))
        _f03_history_exact(self, run)
        result = _f03_history_call(self, 'load', run)
        self.reply_run = result
        self.legacy_run = None
        return result
    run = _f03_history_original_load(self, name)
    _f03_history_select(run)
    return run

Runner.load = _f03_history_load
'''


def compose_source(base_raw):
    """Append only the pinned readonly seams before the existing final main."""
    if type(base_raw) is not bytes:
        raise ValueError('Exact unadapted Source bytes required')
    text = base_raw.decode('utf-8')
    tree = ast.parse(text)
    if any(isinstance(n, ast.Name) and n.id == '_F03_HISTORY_RUN' for n in ast.walk(tree)):
        raise ValueError('Already adapted Source refused')
    runners = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Runner']
    if len(runners) != 1:
        raise ValueError('One existing Runner required')
    methods = {n.name:n for n in runners[0].body if isinstance(n, ast.FunctionDef)}
    for name, expected in METHOD_PINS.items():
        node = methods.get(name)
        if node is None or hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest() != expected:
            raise ValueError('Readonly Source method changed: ' + name)
    tail = tree.body[-1]
    if not (isinstance(tail, ast.If) and ast.unparse(tail.test) == "__name__ == '__main__'"
            and len(tail.body) == 1 and ast.unparse(tail.body[0]) == 'sys.exit(main())'):
        raise ValueError('Exact final main seam required')
    lines = text.splitlines(keepends=True)
    result = (''.join(lines[:tail.lineno-1]) + SEAM + '\n'
              + ''.join(lines[tail.lineno-1:])).encode()
    ast.parse(result)
    return result


if __name__ == '__main__':
    raise SystemExit('REFUSED: pure Source composition only')
