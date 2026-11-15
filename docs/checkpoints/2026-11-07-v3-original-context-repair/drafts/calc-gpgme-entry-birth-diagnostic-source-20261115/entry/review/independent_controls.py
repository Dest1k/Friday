"""Pure extracted-method controls only; never imports GDB or an actor module."""
import ast
import copy
import hashlib
import json
import os
import stat
import types
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = ROOT.parent / 'candidate/outer/deps/gpgme_engine_gdb.py'
PREDECESSOR = Path('/home/jericho/.cache/FRW-ASTRA-CALC-GPGME-M2-REVIEWED-ROOT-20261115/candidate/outer/deps/gpgme_engine_gdb.py')
raw = SOURCE.read_bytes()
tree = ast.parse(raw, str(SOURCE))
oldtree = ast.parse(PREDECESSOR.read_bytes(), str(PREDECESSOR))
methods = {'install', 'bootstrap_entry', 'engine_entry', 'site', 'queue_stop', 'owned_numbers'}
klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Adapter')
selected = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {'SITE_OFFSETS', 'SITE_BYTES'} for t in n.targets)]
selected += [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'need']
selected.append(ast.ClassDef(name='Adapter', bases=[], keywords=[], body=[n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name in methods], decorator_list=[]))
ns = {'Path': Path}
exec(compile(ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[])), str(SOURCE), 'exec'), ns)
Adapter = ns['Adapter']
BASE = 0x70000000
ENTRY = BASE + ns['SITE_OFFSETS']['engine_entry']
LIBRARY = '/synthetic/review-libgpgme.so.11'
passed = []

def check(name, fn):
    fn()
    passed.append(name)

def assertion(value):
    assert value

def refuses(fn, reason):
    try:
        fn()
    except RuntimeError as e:
        assert str(e) == reason, (str(e), reason)
    else:
        raise AssertionError('Expected refusal: ' + reason)

class Error(Exception):
    pass

def fixture():
    a = Adapter.__new__(Adapter)
    calls = []
    inf = types.SimpleNamespace(num=1, pid=100)
    frame = types.SimpleNamespace(pc=lambda: g.pc, is_valid=lambda: True,
        architecture=lambda: types.SimpleNamespace(name=lambda: 'i386:x86-64'))
    class Breakpoint:
        def __init__(self, spec, internal=False):
            calls.append(('breakpoint', spec, internal))
            self.number = len(g.created) + 1
            self.spec, self.enabled, self.valid = spec, True, True
            self.inferior = None
            g.created.append(self)
        def is_valid(self):
            return self.valid
    class G:
        error = Error
        pc = ENTRY
        address = ENTRY
        owner = LIBRARY
        missing = False
        created = None
        Breakpoint = None
        def selected_inferior(self):
            return inf
        def newest_frame(self):
            return frame
        def parse_and_eval(self, expression):
            calls.append(('parse', expression))
            assert expression in {'&gpgme_get_engine_info', '(void *)&gpgme_get_engine_info'}
            if self.missing:
                raise Error('synthetic missing symbol')
            return self.address
        def solib_name(self, pc):
            calls.append(('owner', pc))
            return self.owner
    g = G()
    g.created, g.Breakpoint = [], Breakpoint
    class Collector:
        mapped = True
        relative_override = None
        bytes_ok = True
        cache = 1
        def maps(self, pid):
            calls.append(('maps', pid))
            return [{'path': LIBRARY}] if self.mapped else []
        def image_binding(self, pid, pin, pc):
            calls.append(('binding', pid, pc))
            return {'load_bias': BASE, 'relative_pc': pc - BASE if self.relative_override is None else self.relative_override}
        def bind_current_environment(self, pid):
            calls.append(('bind_environment', pid))
        def snapshot(self, pid, role, expected_thread):
            calls.append(('snapshot', pid, role, expected_thread))
    c = Collector()
    a.g, a.collector, a.calls, a.inf = g, c, calls, inf
    a.n = {'STATE': {'process': {'pid': 100}}}
    a.m = {'collector_pins': {'library': {'path': LIBRARY}}}
    a.installed, a.bootstrap = False, None
    a.breakpoints, a.handlers, a.retired = [], {}, set()
    a.pending_stop, a.pending = None, None
    a.init_active, a.finished_initialization = False, False
    a.binding, a.init_thread, a.init_stack = None, None, None
    a.original = lambda: (calls.append(('original',)), {'pid': 100})[1]
    a.paper_closed = lambda: calls.append(('paper_closed',))
    a.tid = lambda: [100, 100, 0]
    a.ensure = lambda: calls.append(('ensure',))
    a.reg = lambda name: 0x60000000
    a.context = lambda **kw: calls.append(('context', kw))
    def memory(address, count):
        calls.append(('memory', address, count))
        if address == BASE + 0x55558:
            return c.cache.to_bytes(8, 'little')
        if address == ENTRY:
            return bytes.fromhex(ns['SITE_BYTES']['engine_entry'])[:count] if c.bytes_ok else b'\0' * count
        raise AssertionError('Unexpected synthetic memory request')
    a.memory = memory
    def install_bound_sites(binding):
        calls.append(('bound_sites', copy.deepcopy(binding)))
        a.installed = True
    a.install_bound_sites = install_bound_sites
    return a

def unchanged_except_install():
    old = copy.deepcopy(oldtree)
    new = copy.deepcopy(tree)
    for t in (old, new):
        k = next(n for n in t.body if isinstance(n, ast.ClassDef) and n.name == 'Adapter')
        k.body = [n for n in k.body if not (isinstance(n, ast.FunctionDef) and n.name == 'install')]
    assert ast.dump(old, include_attributes=False) == ast.dump(new, include_attributes=False)
check('all_source_AST_except_install_unchanged', unchanged_except_install)

def numeric_install():
    a = fixture()
    a.install()
    assert len(a.g.created) == len(a.breakpoints) == len(a.handlers) == 1
    bp = a.bootstrap
    assert bp.spec == '*' + hex(ENTRY) and bp.inferior == 1
    assert a.handlers[bp.number][1] == a.bootstrap_entry and a.handlers[bp.number][2] is False
    assert not a.installed and a.binding is None and a.pending is None
    assert not any(x[0] in {'owner', 'binding', 'bind_environment', 'bound_sites', 'ensure', 'context'} for x in a.calls)
check('exact_symbol_address_numeric_location_no_initial_authority', numeric_install)

def predicative_stop():
    a = fixture()
    a.install()
    before = copy.copy(a.calls)
    assert a.bootstrap.stop() is True and a.bootstrap.stop() is True
    assert a.calls == before and a.pending is None
check('stop_predicate_repeat_has_no_protocol_effect', predicative_stop)

for label in ('installed', 'bootstrap_present', 'no_process', 'inferior2', 'library_unmapped'):
    def skip(label=label):
        a = fixture()
        if label == 'installed': a.installed = True
        if label == 'bootstrap_present': a.bootstrap = object()
        if label == 'no_process': a.n['STATE']['process'] = None
        if label == 'inferior2': a.inf.num = 2
        if label == 'library_unmapped': a.collector.mapped = False
        a.install()
        assert not a.g.created and not a.handlers
        assert not any(v[0] == 'parse' for v in a.calls)
    check('install_skip_' + label, skip)

def missing_then_late():
    a = fixture()
    a.g.missing = True
    a.install()
    assert a.bootstrap is None and not a.breakpoints and not a.handlers and not a.g.created
    a.g.missing = False
    a.install()
    assert a.bootstrap.spec == '*' + hex(ENTRY)
    a.install()
    assert len(a.g.created) == 1
check('missing_symbol_no_pending_and_late_DSO_retry_once', missing_then_late)

def map_then_late():
    a = fixture()
    a.collector.mapped = False
    a.install()
    a.collector.mapped = True
    a.install()
    assert len(a.g.created) == 1
check('late_library_then_exact_symbol_install', map_then_late)

def no_guessed_bias():
    a = fixture()
    a.g.address = ENTRY + 17
    a.install()
    assert a.bootstrap.spec == '*' + hex(ENTRY + 17)
    a.g.pc = ENTRY + 17
    refuses(a.bootstrap_entry, 'gpgme_bootstrap_exact_symbol_offset')
    assert not a.installed and a.pending is None
check('symbol_value_used_without_guessed_or_tolerated_offset', no_guessed_bias)

for owner in (None, '/synthetic/interposer.so', '/synthetic/executable-PLT'):
    def wrong_owner(owner=owner):
        a = fixture()
        a.g.owner = owner
        refuses(a.bootstrap_entry, 'gpgme_bootstrap_symbol_owner')
        assert not any(v[0] in {'paper_closed', 'binding', 'bind_environment', 'bound_sites', 'ensure', 'context'} for v in a.calls)
    check('first_stop_owner_refusal_' + str(owner), wrong_owner)

def exact_offset():
    a = fixture()
    a.collector.relative_override = ns['SITE_OFFSETS']['engine_entry'] + 1
    refuses(a.bootstrap_entry, 'gpgme_bootstrap_exact_symbol_offset')
    assert not any(v[0] in {'memory', 'bind_environment', 'bound_sites', 'ensure', 'context'} for v in a.calls)
check('first_stop_relative_offset_exact_no_tolerance', exact_offset)

def exact_bytes():
    a = fixture()
    a.collector.bytes_ok = False
    refuses(a.bootstrap_entry, 'gpgme_exact_site_engine_entry')
    assert not any(v[0] in {'bind_environment', 'bound_sites', 'ensure', 'context'} for v in a.calls)
check('first_stop_entry_bytes_refuse_before_ENV_and_bound_sites', exact_bytes)

def exact_pc():
    a = fixture()
    a.g.pc = ENTRY + 4
    refuses(a.bootstrap_entry, 'gpgme_bootstrap_exact_symbol_offset')
    assert not a.installed
check('prologue_advanced_PC_still_refused', exact_pc)

def first_stop():
    a = fixture()
    a.bootstrap_entry()
    assert a.installed and a.init_active and a.pending == 'CONTINUE'
    labels = [v[0] for v in a.calls]
    expected = ['owner', 'paper_closed', 'original', 'binding', 'binding', 'memory', 'original', 'bind_environment', 'original', 'snapshot', 'bound_sites', 'paper_closed', 'ensure', 'context']
    assert labels == expected, labels
check('first_exact_stop_paper_binding_bytes_ENV_snapshot_sites_then_engine', first_stop)

def cached_stop():
    a = fixture()
    a.bootstrap_entry()
    a.finished_initialization, a.init_active, a.pending = True, False, None
    a.calls.clear()
    a.bootstrap_entry()
    assert a.pending is None
    assert not any(v[0] in {'bind_environment', 'snapshot', 'bound_sites', 'ensure', 'context'} for v in a.calls)
    assert len([v for v in a.calls if v[0] == 'binding']) == 2
check('cached_stop_owner_exact_site_and_list_gate_no_ENV_rebind_or_reinstall', cached_stop)

def cache_cleared():
    a = fixture()
    a.bootstrap_entry()
    a.finished_initialization, a.init_active, a.pending = True, False, None
    a.collector.cache = 0
    refuses(a.bootstrap_entry, 'gpgme_cached_engine_list_changed')
check('cached_stop_cleared_engine_list_refused', cache_cleared)

def event_queue():
    a = fixture()
    a.install()
    event = types.SimpleNamespace(breakpoints=[a.bootstrap])
    assert a.queue_stop(event) is True
    assert a.pending_stop == (a.bootstrap.number, 1, 100, [100, 100, 0], ENTRY)
    assert not a.init_active and a.pending is None
check('exact_breakpoint_event_queued_before_callback_effects', event_queue)

def event_wrong_inferior():
    a = fixture()
    a.install()
    a.inf.num = 2
    event = types.SimpleNamespace(breakpoints=[a.bootstrap])
    refuses(lambda: a.queue_stop(event), 'gpgme_breakpoint_event_inferior')
    assert a.pending_stop is None and a.pending is None
check('foreign_inferior_event_refused_before_bootstrap_callback', event_wrong_inferior)

def event_ambiguous():
    a = fixture()
    a.install()
    event = types.SimpleNamespace(breakpoints=[a.bootstrap, a.bootstrap])
    refuses(lambda: a.queue_stop(event), 'gpgme_ambiguous_or_duplicate_breakpoint_event')
check('ambiguous_breakpoint_event_refused', event_ambiguous)

output = {'schema': 'frw.gpgme-bootstrap-independent-pure-controls.v1',
    'source_ref': {'path': str(SOURCE), 'sha256': hashlib.sha256(raw).hexdigest()},
    'predecessor_ref': {'path': str(PREDECESSOR), 'sha256': hashlib.sha256(PREDECESSOR.read_bytes()).hexdigest()},
    'control_count': len(passed), 'passed': passed,
    'scope': 'SOURCE_ONLY_EXTRACTED_METHODS_SYNTHETIC_GDB_NO_ACTORS_NO_RUNTIME_CREDIT',
    'gdb_address_expression_semantics': 'STATIC_REVIEW_ONLY_NOT_EXECUTED',
    'findings': []}
path = ROOT / 'INDEPENDENT-CONTROLS.json'
path.write_text(json.dumps(output, sort_keys=True, indent=2) + '\n')
path.chmod(0o600)
print(json.dumps({'control_count': len(passed), 'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}, sort_keys=True))
