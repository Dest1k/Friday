"""Optional exact GpgME 2.0.1 observer; no admission is granted by this file.

The adapter reads stopped owned inferiors only.  All breakpoint creation,
retirement and inferior selection occur after GDB returns from callbacks.
Decoded program paths are compared with Root pins, never turned into grants.
"""
import copy
import hashlib
import json
import os
import stat
import types
import struct
import time
from pathlib import Path

MAX_BOUNDARIES = 512
PROCESS_GUARD_COMMANDS = (('clone_guard', 'catch syscall clone clone3'), ('unsupported_process_or_session', 'catch syscall setsid setpgid'), ('exit_intent', 'catch syscall exit exit_group'))
PROCESS_GUARD_KINDS = frozenset((kind for kind, _ in PROCESS_GUARD_COMMANDS))
LIBC_FORK_SYSCALL_RETURN = 0xf70a8
LIBC_FORK_SYSCALL_BYTES = '0f05483d00f0ffff7768'
SITE_OFFSETS = {
    'engine_entry': 0x202d0, 'engine_return': 0x2034c,
    'dirs_parent0': 0x39e51, 'dirs_parent1': 0x39e5e, 'version_parent': 0x203ed,
    'wait_call': 0x377e3, 'wait_return': 0x377e8,
    'spawn_entry': 0x37620, 'first_fork_return': 0x37785,
    'second_fork_return': 0x378c5, 'exec_call': 0x37aae,
    'dirs_entry': 0x38c10, 'dirs_spawn_return': 0x38cf0,
    'dirs_read_call': 0x38d0f, 'dirs_read_return': 0x38d14,
    'dirs_close_call': 0x38d1e, 'dirs_close_return': 0x38d23,
    'version_entry': 0x42a90, 'version_spawn_return': 0x42b7f,
    'version_read_call': 0x42ba5, 'version_read_return': 0x42baa,
    'version_newline_return': 0x42bcb,
    'version_close_call': 0x42be6, 'version_close_return': 0x42beb,
    'version_newline_close_call': 0x42c2d,
    'version_newline_close_return': 0x42c32,
    'version_return': 0x42c11,
}
# The selected file supplies these bytes offline, and the pinned manifest must
# carry the exact same dictionary.  A manifest cannot supply arbitrary sites.
SITE_BYTES = {'engine_entry': 'f30f1efa554889e54157415641554154', 'engine_return': 'c30f1f00488b0551960200660f6f0561', 'dirs_parent0': 'be010000004c89e7e8b2edffff488b05', 'dirs_parent1': '488b05abb701004c89259cb70100595e', 'version_parent': '48894598488b45904885c00f847d0100', 'wait_call': 'e87806fdff83f8ff74e34139c40f840a', 'wait_return': '83f8ff74e34139c40f840a030000418b', 'spawn_entry': 'f30f1efa554889e541574989ff415645', 'first_fork_return': '4189c44189c683f8ff0f843704000085', 'second_fork_return': '4189c485c00f8520020000488b45a848', 'exec_call': 'e81d05fdffbf08000000e833fefcff0f', 'dirs_entry': '55b980000000488d1525ee0000660fef', 'dirs_spawn_return': '5a5983f8ff0f84ad0400004863f3baff', 'dirs_read_call': 'e8cccaffff85c07f308bbd6cfbffffe8', 'dirs_read_return': '85c07f308bbd6cfbffffe8bdcfffff48', 'dirs_close_call': 'e8bdcfffff488b45c864482b04252800', 'dirs_close_return': '488b45c864482b0425280000000f85fc', 'version_entry': 'f30f1efa55660fefc04889e541574156', 'version_spawn_return': '5a5985c00f882e0200000f1f80000000', 'version_read_call': 'e8362cffff85c07e324101c44a8d3c3b', 'version_read_return': '85c07e324101c44a8d3c3bbe0a000000', 'version_newline_return': '4885c075484183fc4e7eba662e0f1f84', 'version_close_call': 'e8f530ffff31ff488b45c864482b0425', 'version_close_return': '31ff488b45c864482b0425280000000f', 'version_newline_close_call': 'e8ae30ffff0fb68570ffffff84c00f84', 'version_newline_close_return': '0fb68570ffffff84c00f84930000003c'}
SITE_BYTES['version_return'] = 'c3660f1f4400004839c30f8247010000'


def need(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def read_ref(ref):
    need(type(ref) is dict and set(ref) == {'path', 'sha256'}, 'gpgme_ref_schema')
    p = Path(ref['path'])
    need(p.is_absolute() and str(p.resolve()) == str(p), 'gpgme_ref_canonical')
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        stamp = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns,
                           s.st_mode, s.st_uid, s.st_nlink)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
             and before.st_uid == os.getuid() and stat.S_IMODE(before.st_mode) == 0o600
             and before.st_size <= 1048576,
             'gpgme_ref_rights_bound')
        raw = os.read(fd, 1048577)
        need(stamp(before) == stamp(os.fstat(fd)) == stamp(p.lstat()), 'gpgme_ref_CAS')
    finally:
        os.close(fd)
    need(len(raw) <= 1048576 and hashlib.sha256(raw).hexdigest() == ref['sha256'],
         'gpgme_ref_hash')
    return raw


def module(ref, name, injected=None):
    ns = {'__name__': name, '__file__': ref['path'], **(injected or {})}
    exec(compile(read_ref(ref), ref['path'], 'exec'), ns)
    return ns


def create(gdb, native, bundle_ref, paper):
    b = json.loads(read_ref(bundle_ref))
    need(type(b) is dict and set(b) == {'schema', 'manifest_ref', 'validator_ref',
         'collector_ref', 'adapter_ref', 'policy_ref', 'mapper_ref', 'runtime', 'evidence_path'}
         and b['schema'] == 'frw.calc.gpgme-engine-init-bundle.v2', 'gpgme_bundle_schema')
    need(b['adapter_ref']['path'] == str(Path(__file__).resolve()), 'gpgme_adapter_source')
    read_ref(b['adapter_ref'])
    validator = module(b['validator_ref'], 'frw_pinned_gpgme_validator')
    binding = {'manifest': b['manifest_ref'], **{role: b[role + '_ref'] for role in
        ('validator', 'collector', 'adapter', 'policy', 'mapper')}}
    modules = validator['load_sources'](binding, read_ref)
    policy_module, mapper_module, collector_module = (modules[role] for role in ('policy', 'mapper', 'collector'))
    p, mapper, collector = policy_module.__dict__, mapper_module.__dict__, collector_module.__dict__
    manifest = json.loads(read_ref(b['manifest_ref']))
    validator['validate_manifest'](manifest, policy_module, collector_module)
    validator['validate_bundle'](b, manifest, policy_module, collector_module)
    need(b['runtime']['manifest_ref'] == b['manifest_ref']
         and b['runtime']['paper_manifest_ref'] == paper.b['manifest_ref']
         and b['runtime']['operation_id'] == paper.b['runtime']['operation_id']
         and b['runtime']['nonce'] == native['CFG']['nonce']
         and b['runtime']['source_sha256'] == paper.b['runtime']['source_sha256']
         and b['runtime']['marker_path'] == paper.b['runtime']['marker_path']
         and b['runtime']['operation_deadline_monotonic'] ==
             paper.b['runtime']['operation_deadline_monotonic'], 'gpgme_same_original_operation')
    need(b['runtime']['evidence_path'] == b['evidence_path'] ==
         '/tmp/friday-metric-work/output/observer-gpgme-engine-init.json',
         'gpgme_evidence_path')
    return Adapter(gdb, native, b, manifest, p, mapper, collector, validator, paper)


class Adapter:
    def __init__(self, gdb, native, bundle, manifest, policy, mapper, collector, validator, paper):
        self.g, self.n, self.b, self.m, self.p = gdb, native, bundle, manifest, policy
        self.paper, self.v = paper, validator
        self.collector = collector['BoundaryCollector'](gdb, native, manifest['collector_pins'], runtime=bundle['runtime'])
        self.breakpoints, self.handlers, self.retired = [], {}, set()
        self.pending_stop = self.pending = None
        self.to_create, self.to_retire = [], []
        self.catchpoints, self.known, self.exits = {}, {}, {}
        self.exit_order = []
        self.exit_intents = {}
        self.exit_completion = None
        self.clone_entries = set()
        self.c, self.installed, self.init_active = None, False, False
        self.bootstrap = None
        self.init_thread = self.init_stack = self.binding = None
        self.read = self.read_terminal = self.pipe_fd = self.write_fd = None
        self.wait_capture = self.spawn_signature = None
        self.wait_observed = False
        self.caller_route = self.caller_thread = None
        self.version_call = self.close_capture = self.cached_call = None
        self.observations = []
        self.finished_at_return = False
        self.finished_initialization = False
        self.refusal = None
        self.process_guards = []
        self.process_guard_registry, self.process_guard_states = {}, {}
        self.process_guard_refusal, self.process_guard_busy = None, False
        self.process_guard_orphans, self.process_guard_inflight = [], None
        self.process_guard_retire_queue = []
        self.boundary_count = 0
        self.fork_pending = None
        self.fork_terminal = False

    def _selection(self):
        inf, thread = self.g.selected_inferior(), self.g.selected_thread()
        need(inf.is_valid() and inf.pid > 0 and thread is not None and thread.is_valid()
             and thread.is_stopped(), 'gpgme_selection_unavailable')
        frame = self.g.selected_frame()
        need(frame is not None and frame.is_valid(), 'gpgme_selection_unavailable')
        level = int(frame.level())
        need(0 <= level < 24, 'gpgme_selection_frame_bound')
        return (inf.num, inf.pid, tuple(thread.ptid), level, int(frame.pc()))

    def _restore_selection(self, saved):
        number, pid, ptid, level, pc = saved
        matches = [i for i in self.g.inferiors() if i.is_valid() and i.num == number and i.pid == pid]
        need(len(matches) == 1, 'gpgme_selection_inferior_stale')
        threads = [t for t in matches[0].threads() if t.is_valid() and tuple(t.ptid) == ptid]
        need(len(threads) == 1 and threads[0].is_stopped(), 'gpgme_selection_thread_stale')
        threads[0].switch()
        frame = self.g.newest_frame()
        for _ in range(level):
            need(frame is not None and frame.is_valid(), 'gpgme_selection_frame_stale')
            frame = frame.older()
        need(frame is not None and frame.is_valid() and int(frame.pc()) == pc,
             'gpgme_selection_frame_changed')
        frame.select()
        need(self._selection() == saved, 'gpgme_selection_restore_failed')

    def _fork_gate(self, descriptor):
        need(type(descriptor) is dict and not self.fork_terminal and self.fork_pending is descriptor
             and self.n['STATE']['error'] is None and self.pending_stop is None
             and self.pending is None and self.init_active,
             'gpgme_pending_fork_terminal_or_reentry')
        need(self.g.parameter('non-stop') is False
             and self.g.parameter('detach-on-fork') is False
             and self.g.parameter('may-call-functions') is False,
             'gpgme_pending_fork_launch_settings')
        # These genuine same-operation observations are made afresh; a saved
        # context or caller-supplied boolean cannot reopen cancellation/expiry.
        self.collector._window()
        need(time.monotonic() < self.b['runtime']['operation_deadline_monotonic'],
             'gpgme_original_deadline_expired')

    def _owned_stop_pcs(self):
        saved = self._selection()
        result = []
        try:
            for inf in self.g.inferiors():
                need(inf.is_valid(), 'gpgme_pending_fork_invalid_inferior')
                if not inf.pid:
                    continue
                if inf.num == 1:
                    identity = self.original()
                else:
                    known = self.known.get(inf.pid)
                    need(known is not None and known['inferior'] == inf.num,
                         'gpgme_pending_fork_foreign_inferior')
                    identity = self.collector.proc(inf.pid)
                    need(identity == known['identity'], 'gpgme_pending_fork_owned_birth_changed')
                for thread in inf.threads():
                    need(thread.is_valid() and thread.is_stopped(), 'gpgme_pending_fork_thread_running')
                    thread.switch()
                    result.append((inf.num, inf.pid, copy.deepcopy(identity), tuple(thread.ptid),
                                   int(self.g.newest_frame().pc())))
                    need(len(result) <= 1024, 'gpgme_pending_fork_thread_bound')
        finally:
            self._restore_selection(saved)
        return result

    def capture_fork(self):
        """Capture only; GDB table mutation is deferred outside callbacks."""
        need(not self.fork_terminal and self.fork_pending is None
             and self.n['STATE']['error'] is None and self.pending is None
             and self.pending_stop is None and not self.to_create and not self.to_retire,
             'gpgme_pending_fork_duplicate_or_stale')
        need(self.c is not None and self.c.current is not None, 'gpgme_unarmed_fork')
        c = self.c.current
        index = len(c['children'])
        need(index in (0, 1), 'gpgme_third_fork')
        self.paper_closed()
        saved = self._selection()
        parent, thread = self.collector.proc(saved[1]), self.tid()
        need(thread == (c['thread'] if index == 0 else [parent['pid'], parent['pid'], 0]),
             'gpgme_fork_exact_calling_thread')
        # Pin the OS birth BEFORE context/proc is allowed to adopt a child.
        token = self.collector.pending_fork_child(parent['pid'], thread[1])
        context, _snap = self.context(role='original' if index == 0 else 'intermediate')
        offset = self.p['FIRST_FORK_RETURN'] if index == 0 else self.p['SECOND_FORK_RETURN']
        frames, frame = [], self.g.newest_frame()
        for _ in range(24):
            if frame is None or not frame.is_valid():
                break
            frames.append(int(frame.pc())); frame = frame.older()
        need(self.binding['load_bias'] + offset in frames
             and (parent['pid'], offset) in self.clone_entries,
             'gpgme_pending_fork_source_or_clone_entry')
        self.collector.image_binding(parent['pid'], self.m['collector_pins']['library'],
                                     self.binding['load_bias'] + offset)
        site = 'first_fork_return' if index == 0 else 'second_fork_return'
        need(self.memory(self.binding['load_bias'] + offset, 16).hex() == SITE_BYTES[site],
             'gpgme_fork_source_bytes_changed')
        signature = self.spawn_signature
        self.string(signature['path_pointer'], signature['image']['path'])
        argv = struct.unpack('<QQQ', self.memory(signature['argv_pointer'], 24))
        need(argv[2] == 0 and self.memory(signature['fdlist_pointer'], 32) == signature['fdlist_raw'],
             'gpgme_fork_factory_arguments_changed')
        self.string(argv[0], signature['image']['path'])
        self.string(argv[1], self.p['OPTIONS'][c['branch']])
        self.collector.pinned_file(signature['image'])
        pcs = self._owned_stop_pcs()
        selectors = [v for v in pcs if v[3] != tuple(thread)]
        need(selectors, 'gpgme_pending_fork_no_distinct_owned_selector')
        descriptor = dict(state='CAPTURED', parent=saved, token=token, index=index,
            selector=min(selectors, key=lambda v: (v[0], v[3])), pcs=pcs, events=0)
        self.fork_pending = descriptor
        self._fork_gate(descriptor)

    def materialization_stop(self, event):
        descriptor = self.fork_pending
        if descriptor is None:
            return False
        self._fork_gate(descriptor)
        need(descriptor['state'] == 'COMMAND' and descriptor['events'] == 0
             and type(event) is self.g.StopEvent and getattr(event, 'details', None) == {}
             and not hasattr(event, 'breakpoints') and not hasattr(event, 'stop_signal'),
             'gpgme_pending_fork_unexpected_reentrant_event')
        token = descriptor['token']
        self.collector.pending_fork_child(token['parent']['pid'], token['thread'][1],
                                         expected=token, materialized=True)
        selected = self.g.selected_inferior()
        need(selected.pid == token['identity']['pid'] and selected.num > 3
             and self.tid() == [selected.pid, selected.pid, 0],
             'gpgme_pending_fork_materialized_selection')
        descriptor['events'] = 1
        descriptor['state'] = 'STOPPED'
        return True

    def materialize_fork(self):
        descriptor = self.fork_pending
        self._fork_gate(descriptor)
        need(descriptor['state'] == 'CAPTURED', 'gpgme_pending_fork_command_already_attempted')
        saved = descriptor['parent']
        settings = {key: self.g.parameter(key) for key in
                    ('follow-fork-mode', 'schedule-multiple', 'scheduler-locking')}
        need(settings == {'follow-fork-mode': 'parent', 'schedule-multiple': True,
                          'scheduler-locking': 'off'}, 'gpgme_pending_fork_runcontrol_changed')
        failure = None
        try:
            need(self._selection() == saved and self._owned_stop_pcs() == descriptor['pcs'],
                 'gpgme_pending_fork_captured_stop_changed')
            self._fork_gate(descriptor)
            token = descriptor['token']
            self.collector.pending_fork_child(token['parent']['pid'], token['thread'][1], expected=token)
            self.context(role='original' if descriptor['index'] == 0 else 'intermediate')
            selector = descriptor['selector']
            self._restore_selection((selector[0], selector[1], selector[3], 0, selector[4]))
            for key, value in (('follow-fork-mode', 'child'), ('schedule-multiple', 'on'),
                               ('scheduler-locking', 'off')):
                self._fork_gate(descriptor)
                self.g.execute('set ' + key + ' ' + value, to_string=True)
                self._fork_gate(descriptor)
            need(self.g.parameter('follow-fork-mode') == 'child'
                 and self.g.parameter('schedule-multiple') is True
                 and self.g.parameter('scheduler-locking') == 'off',
                 'gpgme_pending_fork_settings_readback')
            # Exactly one source-proved table operation, not a target-run
            # fallback. Event/order induction excludes stale pending_follow.
            descriptor['state'] = 'COMMAND'
            self.g.execute('continue', to_string=True)
            self._fork_gate(descriptor)
            need(descriptor['state'] == 'STOPPED' and descriptor['events'] == 1,
                 'gpgme_pending_fork_materialization_event_missing')
            self.collector.pending_fork_child(token['parent']['pid'], token['thread'][1],
                                             expected=token, materialized=True)
            # PCs are extra postconditions; closed GDB source proves no resume.
            for number, pid, identity, ptid, pc in descriptor['pcs']:
                need(self.collector.proc(pid) == identity, 'gpgme_pending_fork_owned_birth_changed')
                self._restore_selection((number, pid, ptid, 0, pc))
            self._restore_selection(saved)
            self._fork_gate(descriptor)
            self.birth()  # unchanged full source/factory/context/policy guards
            self._fork_gate(descriptor)
            child = token['identity']
            known = self.known.get(child['pid'])
            need(known is not None and known['identity'] == child,
                 'gpgme_pending_fork_adopted_birth_changed')
            descriptor['state'] = 'ENROLLING'
            inf = [i for i in self.g.inferiors() if i.is_valid()
                   and i.num == known['inferior'] and i.pid == child['pid']]
            need(len(inf) == 1, 'gpgme_pending_fork_child_inferior_changed')
            self.enroll_process_guards(inf[0])
            self._fork_gate(descriptor)
        except Exception as exc:
            failure = str(exc) if type(exc) is RuntimeError else type(exc).__name__
            self.fork_terminal = True
        finally:
            # Only bounded nonexecuting restoration is allowed after refusal.
            # Do not replace the first refusal with a cleanup failure.
            try:
                for key, value in settings.items():
                    text = ('on' if value else 'off') if type(value) is bool else value
                    self.g.execute('set ' + key + ' ' + text, to_string=True)
                    need(self.g.parameter(key) == value, 'gpgme_pending_fork_restore_settings')
                self._restore_selection(saved)
            except Exception as exc:
                failure = failure or (str(exc) if type(exc) is RuntimeError else type(exc).__name__)
                self.fork_terminal = True
        if failure is not None:
            self.clear_pending()
            raise RuntimeError(failure)
        self._fork_gate(descriptor)
        self.fork_pending = None
        self.pending = 'CONTINUE'

    def _guard_fail(self, reason):
        self.process_guard_refusal = self.process_guard_refusal or reason
        raise RuntimeError(self.process_guard_refusal)

    def _guard_need(self, condition, reason):
        if not condition:
            self._guard_fail(reason)

    def _guard_breakpoint_ok(self, bp):
        self._guard_need(bp.is_valid() and bp.type == self.g.BP_CATCHPOINT and (bp.enabled is True) and (bp.condition is None) and (bp.thread is None) and (bp.inferior is None) and (bp.task is None) and (type(bp.ignore_count) is int) and (bp.ignore_count == 0) and (bp.commands is None), 'gpgme_process_guard_properties_changed')

    def _guard_owner_identity(self, inferior):
        self._guard_need(inferior.is_valid() and type(inferior.num) is int and (inferior.num > 0) and (type(inferior.pid) is int) and (inferior.pid > 0), 'gpgme_process_guard_inferior_unknown')
        if inferior.num == 1:
            actual = self.original()
            self._guard_need(actual['pid'] == inferior.pid, 'gpgme_process_guard_original_changed')
        else:
            known = self.known.get(inferior.pid)
            self._guard_need(inferior.num > 3 and known is not None and (known['inferior'] == inferior.num), 'gpgme_process_guard_child_not_accepted')
            actual = self.collector.proc(inferior.pid)
            self._guard_need(actual == known['identity'] and self.c is not None and (self.c.current is not None) and any((child['inferior'] == inferior.num and child['identity'] == actual for child in self.c.current['children'])), 'gpgme_process_guard_child_birth_changed')
        return actual

    def _guard_snapshot_breakpoints(self):
        values = list(self.g.breakpoints() or ())
        self._guard_need(all((type(bp.number) is int for bp in values)) and len({bp.number for bp in values}) == len(values), 'gpgme_process_guard_breakpoint_number_ambiguity')
        return {bp.number: bp for bp in values}

    def _guard_observed_exited_owner(self, owner):
        return (type(owner) is int and owner > 3
            and owner in self.process_guard_retire_queue
            and not any(inf.is_valid() and inf.num == owner and inf.pid > 0
                        for inf in self.g.inferiors()))

    def _guard_validate_registry(self):
        """Retained active catch objects remain expected even after owner exit."""
        numbers = set()
        objects = set()
        for (owner, kind), entry in self.process_guard_registry.items():
            self._guard_need(type(owner) is int and owner > 0 and (kind in PROCESS_GUARD_KINDS) and (self.process_guard_states.get(owner) == 'ACTIVE') and (entry['owner_number'] == owner) and (entry['category'] == kind), 'gpgme_process_guard_registry_incomplete')
            bp = entry['breakpoint']
            number = entry['number']
            if bp.is_valid():
                self._guard_breakpoint_ok(bp)
                self._guard_need(bp.number == number, 'gpgme_process_guard_registry_duplicate_or_stale')
            else:
                self._guard_need(self._guard_observed_exited_owner(owner),
                    'gpgme_process_guard_live_owner_guard_invalid')
            self._guard_need(number not in numbers and id(bp) not in objects and (self.catchpoints.get(number) == kind), 'gpgme_process_guard_registry_duplicate_or_stale')
            numbers.add(number)
            objects.add(id(bp))
        self._guard_need(len(self.process_guards) == len(self.process_guard_registry) and {id(bp) for bp in self.process_guards} == objects, 'gpgme_process_guard_registry_list_join')
        self._guard_need({number for number, kind in self.catchpoints.items() if kind in PROCESS_GUARD_KINDS} == numbers, 'gpgme_process_guard_catchpoint_map_join')
        for owner, state in self.process_guard_states.items():
            if state == 'ACTIVE':
                self._guard_need({kind for number, kind in self.process_guard_registry if number == owner} == PROCESS_GUARD_KINDS, 'gpgme_process_guard_registry_incomplete')

    def guard_kind(self, event):
        """Exact singleton fork/exec, or all global owned catches of one category."""
        if self.process_guard_refusal is not None:
            raise RuntimeError(self.process_guard_refusal)
        try:
            self._guard_need(not self.process_guard_busy, 'gpgme_process_guard_reentry')
            hits = tuple(getattr(event, 'breakpoints', ()))
            self._guard_need(hits and len({id(bp) for bp in hits}) == len(hits) and (len({bp.number for bp in hits}) == len(hits)) and all((bp.type == self.g.BP_CATCHPOINT for bp in hits)), 'gpgme_ambiguous_catchpoint')
            kinds = [self.catchpoints.get(bp.number) for bp in hits]
            if not any((kind in PROCESS_GUARD_KINDS for kind in kinds)):
                self._guard_need(len(hits) == 1 and kinds[0] in ('fork', 'vfork', 'exec'), 'gpgme_ambiguous_catchpoint')
                return kinds[0]
            self._guard_need(len(set(kinds)) == 1 and kinds[0] in PROCESS_GUARD_KINDS, 'gpgme_process_guard_mixed_category')
            kind = kinds[0]
            self._guard_need(self.n['STATE']['error'] is None and self.init_active, 'gpgme_process_guard_outside_initialization')
            self._guard_validate_registry()
            selected = self.g.selected_inferior()
            identity = self._guard_owner_identity(selected)
            entry = self.process_guard_registry.get((selected.num, kind))
            self._guard_need(entry is not None and self.process_guard_states.get(selected.num) == 'ACTIVE' and (entry['owner_pid'] == identity['pid']) and (entry['owner_start_ticks'] == identity['start_ticks']) and (entry['progspace'] == selected.progspace), 'gpgme_process_guard_selected_not_enrolled')
            expected = {entry['number']: entry['breakpoint'] for (owner, category), entry in self.process_guard_registry.items()
                if category == kind and entry['breakpoint'].is_valid()}
            self._guard_need(len(hits) == len(expected) and all((expected.get(bp.number) is bp for bp in hits)), 'gpgme_process_guard_event_set_changed')
            return kind
        except Exception as exc:
            self._guard_fail(str(exc) if type(exc) is RuntimeError else type(exc).__name__)

    def enroll_process_guards(self, inferior):
        """One enrollment attempt per accepted inferior; no implicit partial retry."""
        if self.process_guard_refusal is not None:
            raise RuntimeError(self.process_guard_refusal)
        owner = None
        saved = None
        try:
            self._guard_need(not self.process_guard_busy and self.n['STATE']['error'] is None and self.init_active and (self.g.parameter('non-stop') is False), 'gpgme_process_guard_enrollment_unavailable')
            identity = self._guard_owner_identity(inferior)
            owner = inferior.num
            threads = list(inferior.threads())
            self._guard_need(threads and all((t.is_valid() and t.is_stopped() and (tuple(t.ptid)[0] == inferior.pid) for t in threads)), 'gpgme_process_guard_target_not_stopped')
            existing = self.process_guard_states.get(owner)
            if existing == 'ACTIVE':
                self._guard_validate_registry()
                for kind in PROCESS_GUARD_KINDS:
                    entry = self.process_guard_registry[owner, kind]
                    self._guard_need(entry['owner_pid'] == identity['pid'] and entry['owner_start_ticks'] == identity['start_ticks'] and (entry['progspace'] == inferior.progspace), 'gpgme_process_guard_owner_reused')
                return
            self._guard_need(existing is None and (not any((number == owner for number, kind in self.process_guard_registry))), 'gpgme_process_guard_enrollment_already_attempted')
            self._guard_validate_registry()
            saved = self._selection()
            self.process_guard_states[owner] = 'ENROLLING'
            self.process_guard_busy = True
            if self.g.selected_inferior().num != owner:
                min(threads, key=lambda t: tuple(t.ptid)).switch()
            self._guard_need(self.g.selected_inferior() is inferior and self.g.selected_inferior().progspace == inferior.progspace, 'gpgme_process_guard_selection_changed')
            for kind, command in PROCESS_GUARD_COMMANDS:
                self._guard_need(self.n['STATE']['error'] is None and self._guard_owner_identity(inferior) == identity and (self.g.selected_inferior() is inferior), 'gpgme_process_guard_owner_changed_during_enrollment')
                before = self._guard_snapshot_breakpoints()
                self.process_guard_inflight = (owner, kind, before)
                execution_error = None
                try:
                    self.g.execute(command, to_string=True)
                except Exception as exc:
                    execution_error = exc
                after = self._guard_snapshot_breakpoints()
                added = [bp for number, bp in after.items() if number not in before]
                self.process_guard_orphans.extend((dict(owner_number=owner, category=kind, breakpoint=bp,
                    number=bp.number, delete_attempted=False) for bp in added))
                self.process_guard_inflight = None
                self._guard_need(all((after.get(number) is bp for number, bp in before.items())), 'gpgme_process_guard_existing_breakpoints_changed')
                if execution_error is not None:
                    self._guard_fail(type(execution_error).__name__)
                self._guard_need(len(added) == 1, 'gpgme_exact_process_guard_install')
                bp = added[0]
                self._guard_breakpoint_ok(bp)
                self._guard_need(self.n['STATE']['error'] is None and self.g.selected_inferior() is inferior and (self._guard_owner_identity(inferior) == identity), 'gpgme_process_guard_owner_changed_during_enrollment')
                self.process_guard_registry[owner, kind] = dict(owner_number=owner, owner_pid=identity['pid'], owner_start_ticks=identity['start_ticks'], progspace=inferior.progspace, category=kind, breakpoint=bp, number=bp.number, delete_attempted=False)
                self.process_guards.append(bp)
                self.catchpoints[bp.number] = kind
                self.process_guard_orphans[:] = [entry for entry in self.process_guard_orphans if entry['breakpoint'] is not bp]
            self.process_guard_states[owner] = 'ACTIVE'
            self._guard_validate_registry()
        except Exception as exc:
            if owner is not None and self.process_guard_states.get(owner) == 'ENROLLING':
                self.process_guard_states[owner] = 'FAILED'
            self.process_guard_refusal = self.process_guard_refusal or (str(exc) if type(exc) is RuntimeError else type(exc).__name__)
            raise RuntimeError(self.process_guard_refusal) from None
        finally:
            if saved is not None:
                try:
                    self._restore_selection(saved)
                except Exception as exc:
                    self.process_guard_refusal = self.process_guard_refusal or (str(exc) if type(exc) is RuntimeError else type(exc).__name__)
                    if owner is not None and self.process_guard_states.get(owner) != 'RETIRED':
                        self.process_guard_states[owner] = 'FAILED'
                    raise RuntimeError(self.process_guard_refusal) from None
                finally:
                    self.process_guard_busy = False

    def retire_process_guards(self, inferior_number=None):
        """One deletion attempt per retained object, including partial creation.

    Runs during normal finish or explicit refused-source cleanup. A failed
    deletion is retained as RETIRE_FAILED and is never implicitly repeated.
    """
        self._guard_need(not self.process_guard_busy, 'gpgme_process_guard_retirement_reentry')
        self._guard_need(self.process_guard_inflight is None, 'gpgme_process_guard_creation_unknown')
        owners = {owner for owner, state in self.process_guard_states.items() if state != 'RETIRED'} if inferior_number is None else {inferior_number}
        self._guard_need(all((type(owner) is int and owner in self.process_guard_states for owner in owners)), 'gpgme_process_guard_retirement_unknown_owner')
        self._guard_need(not any((self.process_guard_states.get(owner) in ('RETIRING', 'RETIRE_FAILED') for owner in owners)), 'gpgme_process_guard_retirement_already_attempted')
        entries = [entry for (owner, kind), entry in self.process_guard_registry.items() if owner in owners]
        entries += [entry for entry in self.process_guard_orphans if entry['owner_number'] in owners]
        self._guard_need(not any((entry['delete_attempted'] for entry in entries)), 'gpgme_process_guard_retirement_already_attempted')
        for owner in owners:
            self.process_guard_states[owner] = 'RETIRING'
        seen = set()
        try:
            for entry in entries:
                bp = entry['breakpoint']
                self._guard_need(id(bp) not in seen, 'gpgme_process_guard_retirement_duplicate')
                seen.add(id(bp))
                number = entry['number']
                entry['delete_attempted'] = True
                if bp.is_valid():
                    bp.delete()
                else:
                    self._guard_need(self._guard_observed_exited_owner(entry['owner_number']),
                        'gpgme_process_guard_live_owner_guard_invalid')
                self._guard_need(not bp.is_valid(), 'gpgme_process_guard_retirement')
                self.catchpoints.pop(number, None)
                self.process_guards[:] = [owned for owned in self.process_guards if owned is not bp]
                self.process_guard_orphans[:] = [orphan for orphan in self.process_guard_orphans if orphan['breakpoint'] is not bp]
                self.process_guard_registry.pop((entry['owner_number'], entry['category']), None)
            for owner in owners:
                self.process_guard_states[owner] = 'RETIRED'
            self.process_guard_retire_queue[:] = [owner for owner in self.process_guard_retire_queue if owner not in owners]
        except Exception as exc:
            for owner in owners:
                self.process_guard_states[owner] = 'RETIRE_FAILED'
            self.process_guard_refusal = self.process_guard_refusal or (str(exc) if type(exc) is RuntimeError else type(exc).__name__)
            raise RuntimeError(self.process_guard_refusal) from None


    def owned_numbers(self):
        return set(self.handlers) | self.retired

    def tid(self):
        t = self.g.selected_thread()
        need(t is not None and t.is_valid(), 'gpgme_thread_unknown')
        return list(t.ptid)

    def reg(self, name):
        v = self.g.newest_frame().read_register(name)
        need(not v.is_unavailable and not v.is_optimized_out, 'gpgme_register_unavailable')
        return int(v) & ((1 << 64) - 1)

    def signed(self, name, bits=32):
        v = self.reg(name) & ((1 << bits) - 1)
        return v - (1 << bits) if v >= 1 << (bits - 1) else v

    def memory(self, address, count):
        need(type(address) is int and address > 0 and type(count) is int
             and 0 < count <= 4096, 'gpgme_memory_bound')
        return self.g.selected_inferior().read_memory(address, count).tobytes()

    def string(self, address, expected):
        raw = expected.encode('utf-8') + b'\0'
        need(len(raw) <= 4096 and self.memory(address, len(raw)) == raw,
             'gpgme_exact_string_mismatch')

    def original(self):
        value = self.n['STATE']['process']
        need(value is not None, 'gpgme_original_unbound')
        actual = self.collector.proc(value['pid'])
        need(actual['pid'] == value['pid'] and actual['start_ticks'] == value['start_ticks']
             and actual['ppid'] == value['gdb_pid'] == os.getpid(), 'gpgme_original_identity')
        return actual

    def site(self, name, frame=None):
        frame = frame or self.g.newest_frame()
        need(frame is not None and frame.is_valid() and
             frame.architecture().name() == 'i386:x86-64', 'gpgme_frame_architecture')
        pc = int(frame.pc())
        binding = self.collector.image_binding(self.g.selected_inferior().pid,
            self.m['collector_pins']['library'], pc)
        need(binding['load_bias'] + SITE_OFFSETS[name] == pc
             and self.memory(pc, len(bytes.fromhex(SITE_BYTES[name]))).hex() == SITE_BYTES[name],
             'gpgme_exact_site_' + name)
        return binding

    def context(self, *, role='original', thread=None):
        # Collector establishes these observations from the actual current
        # all-stop point.  Supplied protocol booleans are never a substitute.
        snap = self.collector.snapshot(self.original()['pid'], role, expected_thread=thread)
        context = snap['context']
        need(context['operation_id'] == self.b['runtime']['operation_id']
             and context['nonce'] == self.b['runtime']['nonce']
             and context['deadline_monotonic'] == self.b['runtime']['operation_deadline_monotonic'],
             'gpgme_collector_operation_binding')
        self.boundary_count += 1
        need(self.boundary_count <= MAX_BOUNDARIES, 'gpgme_boundary_count')
        return context, snap

    def record(self, stage, snapshot):
        need(len(self.observations) < 11 and stage not in [v['stage'] for v in self.observations],
             'gpgme_observation_duplicate_or_bound')
        # The collector snapshot can contain private environment in memory;
        # only its canonical digest is retained in the evidence.
        digest = hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        self.observations.append({'stage': stage, 'sha256': digest})

    def paper_closed(self):
        need(self.paper.c is not None and self.paper.c.e['state'] == 'CLOSED'
             and len(self.paper.c.e['children']) == 2
             and sorted(c['inferior'] for c in self.paper.c.e['children']) == [2, 3],
             'gpgme_requires_observed_paper_closed_inferiors_2_3')
        need(all(not (Path('/proc') / str(c['pid'])).exists()
                 for c in self.paper.c.e['children']), 'gpgme_paper_descendant_present')

    def ensure(self):
        if self.c is None:
            self.paper_closed()
            context, snap = self.context(thread=self.tid())
            env = snap['environment']
            op = {k: context[k] for k in ('operation_id', 'nonce', 'deadline_monotonic')}
            self.c = self.p['EngineInitPreparation'](self.m['profile'], self.original(), op, env,
                source_mode=self.m['source_mode'], helpers=self.m['helpers'],
                reaper=self.collector.reaper)
        return self.c

    def breakpoint(self, address, fn, inferior=1, one_shot=False):
        # GNU17.1's numeric-address decoder uses CURRENT progspace even when
        # the inferior setter supplies a different search_pspace.  Deferred
        # child sites must therefore be created and restricted while that
        # exact stopped owner is selected, not under the restored fork parent.
        saved = self._selection()
        targets = [i for i in self.g.inferiors() if i.is_valid()
                   and i.num == inferior and i.pid > 0]
        need(len(targets) == 1, 'gpgme_breakpoint_owner_unavailable')
        target = targets[0]
        if inferior == 1:
            need(self.original()['pid'] == target.pid, 'gpgme_breakpoint_original_changed')
        else:
            known = self.known.get(target.pid)
            need(known is not None and known['inferior'] == inferior
                 and self.collector.proc(target.pid) == known['identity']
                 and self.c is not None and self.c.current is not None
                 and any(c['inferior'] == inferior and c['identity'] == known['identity']
                         for c in self.c.current['children']), 'gpgme_breakpoint_child_birth_changed')
        threads = list(target.threads())
        need(threads and all(t.is_valid() and t.is_stopped() for t in threads),
             'gpgme_breakpoint_owner_not_stopped')
        selected = [t for t in threads if tuple(t.ptid) == saved[2]]
        if not selected:
            expected = self.init_thread if inferior == 1 else [target.pid, target.pid, 0]
            selected = [t for t in threads if list(t.ptid) == expected]
        need(len(selected) == 1, 'gpgme_breakpoint_owner_thread_unknown')
        class ObservationBreakpoint(self.g.Breakpoint):
            def stop(self):
                # GDB predicates may run more than once: no protocol mutation.
                return True
        bp, failure = None, None
        try:
            selected[0].switch()
            need(self.g.selected_inferior() is target, 'gpgme_breakpoint_owner_selection_changed')
            bp = ObservationBreakpoint('*' + hex(address), internal=True)
            bp.inferior = inferior
            need(bp.inferior == inferior, 'gpgme_breakpoint_inferior')
            locations = list(bp.locations)
            groups = {i.num for i in self.g.inferiors() if i.is_valid()
                      and i.progspace == target.progspace}
            need(len(locations) == 1 and locations[0].owner is bp
                 and locations[0].enabled is True and locations[0].address == address
                 and set(locations[0].thread_groups) == groups and inferior in groups,
                 'gpgme_breakpoint_location_owner_or_address')
        except Exception as exc:
            failure = exc
        finally:
            try:
                self._restore_selection(saved)
            except Exception as exc:
                failure = failure or exc
        if failure is not None:
            # No partial breakpoint may become an untracked continuation.
            # Keep the true exception active for OwnC's private origin capture.
            try:
                raise failure
            except Exception as exc:
                self.n['fail'](str(exc) if type(exc) is RuntimeError else type(exc).__name__)
                if bp is not None and bp.is_valid():
                    try:
                        bp.delete()
                        need(not bp.is_valid(), 'gpgme_breakpoint_failed_creation_still_valid')
                    except Exception:
                        # First refusal stays fixed; native finally owns process
                        # cleanup and no further resume is allowed.
                        pass
                raise
        self.breakpoints.append(bp)
        self.handlers[bp.number] = (bp, fn, one_shot)
        return bp

    def install(self):
        if self.installed or self.bootstrap is not None or self.n['STATE']['process'] is None or self.g.selected_inferior().num != 1:
            return
        # Bootstrap by the exact exported symbol, never by a guessed load base.
        # This observer stop grants no continuation. Numeric breakpoints are
        # installed only after the real stopped boundary has the accepted
        # host/namespace release and exact backing-file/PT_LOAD/CAS proof.
        try:
            rows = self.collector.maps(self.original()['pid'])
            if not any(row['path'] == self.m['collector_pins']['library']['path'] for row in rows):
                return
            adapter = self
            class Bootstrap(self.g.Breakpoint):
                def stop(self):
                    return True
            # A function linespec may skip its prologue. Resolve its address
            # without evaluating a call, then use an address location so the
            # first instruction (and its original ABI) is observed exactly.
            # Missing late-DSO symbols raise gdb.error before a breakpoint is
            # created; the existing load/new_objfile path can retry safely.
            address = int(self.g.parse_and_eval('&gpgme_get_engine_info'))
            bp = Bootstrap('*' + hex(address), internal=True)
            bp.inferior = 1
            need(bp.inferior == 1, 'gpgme_bootstrap_original_inferior')
            self.bootstrap = bp
            self.breakpoints.append(bp)
            self.handlers[bp.number] = (bp, self.bootstrap_entry, False)
        except self.g.error:
            return  # Exact symbol not loaded yet; no numeric fallback.

    def bootstrap_entry(self):
        # Any interposed/different owner is refused before a helper can fork.
        pc = int(self.g.newest_frame().pc())
        owner = self.g.solib_name(pc)
        need(owner is not None and str(Path(owner).resolve()) == self.m['collector_pins']['library']['path'],
             'gpgme_bootstrap_symbol_owner')
        self.paper_closed()
        binding = self.collector.image_binding(self.original()['pid'], self.m['collector_pins']['library'], pc)
        need(binding['relative_pc'] == SITE_OFFSETS['engine_entry'], 'gpgme_bootstrap_exact_symbol_offset')
        self.binding = binding
        self.site('engine_entry')
        if not self.installed:
            # Office can change non-font environment after exec. Freeze the
            # complete effective parent ENV once at this source-bound stop;
            # startup pins and kernel exec ENV cannot stand in for it. Later
            # cached getters keep their existing read-only engine_entry gate.
            self.collector.bind_current_environment(self.original()['pid'])
            self.collector.snapshot(self.original()['pid'], 'original', expected_thread=self.tid())
            self.install_bound_sites(binding)
        self.engine_entry()

    def install_bound_sites(self, binding):
        handlers = {'engine_return': self.engine_return,
            'dirs_entry': self.dirs_entry, 'version_entry': self.version_entry,
            'wait_call': self.wait_call, 'wait_return': self.wait_return,
            'spawn_entry': self.spawn_entry, 'dirs_spawn_return': self.spawn_return,
            'version_spawn_return': self.spawn_return,
            'dirs_read_call': self.read_call, 'version_read_call': self.read_call,
            'dirs_read_return': self.read_return, 'version_read_return': self.read_return,
            'version_newline_return': self.newline_return,
            'dirs_close_call': self.close_call, 'version_close_call': self.close_call,
            'version_newline_close_call': self.close_call,
            'dirs_close_return': self.close_return, 'version_close_return': self.close_return,
            'version_newline_close_return': self.close_return,
            'version_return': self.version_return}
        need(set(SITE_BYTES) == set(SITE_OFFSETS), 'gpgme_source_site_bytes_incomplete')
        for name, fn in handlers.items():
            address = binding['load_bias'] + SITE_OFFSETS[name]
            need(self.memory(address, len(bytes.fromhex(SITE_BYTES[name]))).hex() == SITE_BYTES[name],
                 'gpgme_install_site_bytes')
            self.breakpoint(address, lambda name=name, fn=fn: (self.site(name), fn())[1])
        self.installed = True

    def engine_entry(self):
        if self.finished_initialization:
            need(not self.init_active and self.g.selected_inferior().num == 1
                 and self.cached_call is None and self.version_call is None
                 and self.close_capture is None
                 and int.from_bytes(self.memory(self.binding['load_bias'] + 0x55558, 8), 'little') != 0,
                 'gpgme_cached_engine_list_changed')
            self.context(thread=self.tid())
            self.cached_call = {'thread': self.tid(), 'stack': self.reg('rsp')}
            return
        self.paper_closed()
        need(not self.init_active and not self.finished_initialization
             and self.g.selected_inferior().num == 1 and self.cached_call is None
             and self.version_call is None and self.close_capture is None,
             'gpgme_repeated_or_foreign_engine_initialization')
        self.ensure()
        self.init_active, self.init_thread, self.init_stack = True, self.tid(), self.reg('rsp')
        self.context(thread=self.init_thread)
        # Watch only the finite initialization window.  Unknown process/session
        # changes during this window are terminal.  Creation stays in dispatch.
        self.pending = 'CONTINUE'

    def dirs_entry(self):
        need(self.init_active and self.tid() == self.init_thread and self.c.current is None
             and self.version_call is None and self.close_capture is None,
             'gpgme_dirs_outside_initialization')
        components = self.reg('rsi') & 0xffffffff
        need(components in (0, 1), 'gpgme_dirs_components')
        older = self.g.newest_frame().older()
        expected = 0x39e51 if components == 0 else 0x39e5e
        binding = self.collector.image_binding(self.original()['pid'],
            self.m['collector_pins']['library'], int(older.pc()))
        need(int(older.pc()) - binding['load_bias'] == expected,
             'gpgme_dirs_exact_get_item_caller')
        self.site('dirs_parent1' if components else 'dirs_parent0', older)
        self.caller_route = 'list_components' if components else 'list_dirs'
        self.caller_thread = self.tid()
        helper = self.m['helpers'].get('gpgconf')
        need(helper is not None, 'gpgme_gpgconf_pin_missing')
        self.string(self.reg('rdi'), helper['path'])

    def version_entry(self):
        need(self.init_active and self.tid() == self.init_thread and self.c.current is None
             and self.version_call is None and self.close_capture is None,
             'gpgme_version_outside_initialization')
        self.context(thread=self.init_thread)
        older = self.g.newest_frame().older()
        # Optimized version callbacks tail-call this function.  The actual
        # engine loop callsite and protocol register are both checked.
        b = self.collector.image_binding(self.original()['pid'],
            self.m['collector_pins']['library'], int(older.pc()))
        need(int(older.pc()) - b['load_bias'] == 0x203ed, 'gpgme_version_engine_loop_caller')
        self.site('version_parent', older)
        proto = self.reg('r14') & 0xffffffff
        route = {0: 'gpg_version', 1: 'gpgsm_version', 2: 'gpgconf_version', 4: 'g13_version'}.get(proto)
        need(route is not None, 'gpgme_version_protocol')
        stack, return_pc = self.reg('rsp'), int(older.pc())
        need(int.from_bytes(self.memory(stack, 8), 'little') == return_pc,
             'gpgme_version_entry_stack')
        helper = self.m['helpers'].get(self.p['ROLES'][route])
        null_file = self.reg('rdi') == 0
        if null_file:
            # The engine loop asks for a version before skipping a missing
            # engine name.  The pinned absent helper has no pipe or spawn.
            need(helper is None, 'gpgme_version_null_pinned_helper')
        else:
            need(helper is not None, 'gpgme_version_helper_pin_missing')
            self.string(self.reg('rdi'), helper['path'])
        self.version_call = {'thread': self.tid(), 'stack': stack,
            'return_pc': return_pc, 'route': route, 'null_file': null_file,
            'spawned': False, 'read_closed': False, 'null_epilogue': False}
        self.caller_route, self.caller_thread = (None if null_file else route), self.tid()

    def version_frame(self, *, at_return=False):
        call = self.version_call
        need(call is not None and self.init_active and self.tid() == self.init_thread == call['thread'],
             'gpgme_version_unmatched_frame')
        stack = self.reg('rsp') if at_return else self.reg('rbp') + 8
        older = self.g.newest_frame().older()
        need(stack == call['stack'] and older is not None
             and int(older.pc()) == call['return_pc']
             and int.from_bytes(self.memory(stack, 8), 'little') == call['return_pc'],
             'gpgme_version_frame_changed')
        self.site('version_parent', older)
        return call

    def version_return(self):
        self.context(thread=self.init_thread)
        call = self.version_frame(at_return=True)
        need(self.close_capture is None and self.c.current is None and self.read is None,
             'gpgme_version_return_unclosed')
        if call['null_file']:
            need(call['null_epilogue'] and not call['spawned'] and not call['read_closed']
                 and self.reg('rax') == 0, 'gpgme_version_null_return_changed')
        else:
            need(call['spawned'] and call['read_closed'], 'gpgme_version_return_without_read_close')
        self.version_call = None
        self.caller_route = self.caller_thread = None

    def spawn_entry(self):
        self.paper_closed()
        need(self.init_active and self.tid() == self.init_thread == self.caller_thread
             and self.caller_route in self.p['BRANCHES'], 'gpgme_unknown_spawn_factory')
        context, snap = self.context(thread=self.init_thread)
        branch = self.caller_route
        if branch in self.p['VERSIONS']:
            call = self.version_call
            need(call is not None and not call['null_file'] and not call['spawned']
                 and call['route'] == branch and call['thread'] == self.tid()
                 and self.reg('rbp') + 8 == call['stack']
                 and int.from_bytes(self.memory(call['stack'], 8), 'little') == call['return_pc'],
                 'gpgme_version_spawn_lifecycle')
        expected_return = 0x38cf0 if branch in self.p['BRANCHES'][:2] else 0x42b7f
        older = self.g.newest_frame().older()
        need(int(older.pc()) - self.binding['load_bias'] == expected_return
             and int.from_bytes(self.memory(self.reg('rsp'), 8), 'little') == int(older.pc()),
             'gpgme_spawn_exact_caller_stack')
        self.site('dirs_spawn_return' if branch in self.p['BRANCHES'][:2] else 'version_spawn_return', older)
        image = self.m['helpers'][self.p['ROLES'][branch]]
        self.collector.pinned_file(image)
        self.string(self.reg('rdi'), image['path'])
        argv = struct.unpack('<QQQ', self.memory(self.reg('rsi'), 24))
        need(argv[2] == 0, 'gpgme_argv_exact_two')
        self.string(argv[0], image['path'])
        self.string(argv[1], self.p['OPTIONS'][branch])
        need(self.reg('rdx') == 1 and self.reg('r8') == self.reg('r9') == 0
             and int.from_bytes(self.memory(self.reg('rsp') + 8, 8), 'little') == 0,
             'gpgme_spawn_flags_callbacks_rpid')
        # Exact LP64 spawn_fd_item_s: fd,dup_to,peer_name,arg_loc (four int32).
        first = struct.unpack('<iiii', self.memory(self.reg('rcx'), 16))
        sentinel = struct.unpack('<iiii', self.memory(self.reg('rcx') + 16, 16))
        need(first[0] > 2 and first[1:] == (1, -1, 0)
             and sentinel == (-1, -1, 0, 0), 'gpgme_spawn_fdlist_exact')
        write = self.collector.fd(self.original()['pid'], first[0])
        fds = self.collector.fds(self.original()['pid'])
        opposite = [number for number, value in fds.items() if number != first[0]
            and value['access'] == os.O_RDONLY and all(value[k] == write[k]
            for k in ('dev', 'ino', 'type', 'rdev'))]
        need(len(opposite) == 1, 'gpgme_parent_pipe_pair_ambiguous')
        self.pipe_fd, self.write_fd = opposite[0], first[0]
        self.spawn_signature = {'path_pointer': self.reg('rdi'), 'argv_pointer': self.reg('rsi'),
            'fdlist_pointer': self.reg('rcx'), 'fdlist_raw': self.memory(self.reg('rcx'), 32),
            'image': copy.deepcopy(image)}
        self.wait_capture, self.wait_observed = None, False
        self.observations = []
        self.c.arm(context, branch, self.tid(), [image['path'], self.p['OPTIONS'][branch]],
            image, fds[self.pipe_fd], write, source_route=branch)
        self.record('arm', snap)
        self.read, self.read_terminal = None, None
        if branch in self.p['VERSIONS']:
            self.version_call['spawned'] = True

    def birth(self):
        need(self.c is not None and self.c.current is not None, 'gpgme_unarmed_fork')
        c = self.c.current
        n = len(c['children'])
        need(n in (0, 1), 'gpgme_third_fork')
        context, snap = self.context(role='original' if n == 0 else 'intermediate')
        parent = self.collector.proc(self.g.selected_inferior().pid)
        thread = self.tid()
        need(thread == (c['thread'] if n == 0 else [parent['pid'], parent['pid'], 0]),
             'gpgme_fork_exact_calling_thread')
        frames, frame = [], self.g.newest_frame()
        for _ in range(24):
            if frame is None or not frame.is_valid():
                break
            frames.append(int(frame.pc()))
            frame = frame.older()
        expected_offset = self.p['FIRST_FORK_RETURN'] if n == 0 else self.p['SECOND_FORK_RETURN']
        need(self.binding['load_bias'] + expected_offset in frames, 'gpgme_fork_exact_source_return')
        self.collector.image_binding(parent['pid'], self.m['collector_pins']['library'],
            self.binding['load_bias'] + expected_offset)
        site_name = 'first_fork_return' if n == 0 else 'second_fork_return'
        need(self.memory(self.binding['load_bias'] + expected_offset, 16).hex() == SITE_BYTES[site_name],
             'gpgme_fork_source_bytes_changed')
        signature = self.spawn_signature
        self.string(signature['path_pointer'], signature['image']['path'])
        argv = struct.unpack('<QQQ', self.memory(signature['argv_pointer'], 24))
        need(argv[2] == 0 and self.memory(signature['fdlist_pointer'], 32) == signature['fdlist_raw'],
             'gpgme_fork_factory_arguments_changed')
        self.string(argv[0], signature['image']['path'])
        self.string(argv[1], self.p['OPTIONS'][c['branch']])
        self.collector.pinned_file(signature['image'])
        child_pids = self.collector.children(parent['pid'], thread[1])
        need(len(child_pids) == 1, 'gpgme_fork_exact_direct_child')
        child = self.collector.proc(child_pids[0])
        matches = [i for i in self.g.inferiors() if i.pid == child['pid']]
        need(len(matches) == 1 and matches[0].num > 3, 'gpgme_fork_child_inferior')
        need((parent['pid'], expected_offset) in self.clone_entries,
             'gpgme_fork_without_observed_exact_clone_entry')
        self.c.birth(context, parent, child, matches[0].num,
            event='fork', return_offset=expected_offset, thread=thread)
        self.known[child['pid']] = dict(identity=child, inferior=matches[0].num)
        self.record('birth' + str(n + 1), snap)
        if n == 1:
            # Final child still shares the exact original image until exec.
            self.to_create.append((self.binding['load_bias'] + SITE_OFFSETS['exec_call'],
                self.exec_call, matches[0].num, True))

    def refresh_reparent(self, context, snap):
        c = self.c.current
        if c is None or len(c['children']) != 2:
            return
        final = c['children'][1]
        if final['exit_code'] is not None or not (Path('/proc') / str(final['identity']['pid'])).exists():
            return
        actual = self.collector.proc(final['identity']['pid'])
        if actual == final['identity']:
            return
        need(c['children'][0]['exit_code'] == 0, 'gpgme_reparent_before_observed_parent_exit')
        reaper = self.collector.proc(self.collector.reaper['pid'])
        need(reaper == self.collector.reaper, 'gpgme_reaper_birth_changed')
        self.c.reparent(context, actual, exact_reaper_identity=reaper,
            old_parent_absent=not (Path('/proc') / str(c['children'][0]['identity']['pid'])).exists())
        self.known[actual['pid']]['identity'] = actual
        self.record('reparent', snap)

    def exec_call(self):
        self.site('exec_call')
        context, snap = self.context(role='final')
        self.flush_exits(context, snap)
        self.refresh_reparent(context, snap)
        c = self.c.current
        need(c is not None and len(c['children']) == 2
             and self.g.selected_inferior().num == c['children'][1]['inferior'],
             'gpgme_exec_call_final_identity')
        image = self.m['helpers'][c['role']]
        self.string(self.reg('rdi'), image['path'])
        argv = struct.unpack('<QQQ', self.memory(self.reg('rsi'), 24))
        need(argv[2] == 0, 'gpgme_exec_call_argv_length')
        self.string(argv[0], image['path'])
        self.string(argv[1], self.p['OPTIONS'][c['branch']])
        self.collector.pinned_file(image)

    def exec_stop(self):
        context, snap = self.context(role='final')
        self.flush_exits(context, snap)
        self.refresh_reparent(context, snap)
        c = self.c.current
        need(c is not None and len(c['children']) == 2, 'gpgme_unknown_exec')
        child = self.collector.proc(self.g.selected_inferior().pid)
        need(self.g.selected_inferior().num == c['children'][1]['inferior'], 'gpgme_exec_inferior')
        image = self.m['helpers'][c['role']]
        self.collector.exec_image(child['pid'], image,
            [image['path'], self.p['OPTIONS'][c['branch']]])
        env = self.collector.exec_environment(child['pid'])
        fds = self.collector.fds(child['pid'])
        self.collector.dependencies(child['pid'], c['role'], entry=False)
        self.c.exec_before_execution(context, child, image,
            [image['path'], self.p['OPTIONS'][c['branch']]], fds, env,
            null_rdev=Path('/dev/null').stat().st_rdev, event='exec_before_first_instruction')
        self.record('exec', snap)
        entry = self.collector.entry_address(child['pid'], c['role'])
        self.to_create.append((entry, self.entry, c['children'][1]['inferior'], True))

    def entry(self):
        context, snap = self.context(role='final')
        self.flush_exits(context, snap)
        self.refresh_reparent(context, snap)
        c = self.c.current
        child = self.collector.proc(self.g.selected_inferior().pid)
        self.collector.dependencies(child['pid'], c['role'], entry=True)
        self.collector.verify_entry(child['pid'], c['role'], int(self.g.newest_frame().pc()))
        self.collector.exec_image(child['pid'], self.m['helpers'][c['role']],
            [self.m['helpers'][c['role']]['path'], self.p['OPTIONS'][c['branch']]])
        self.p['validate_exec_fds'](self.collector.fds(child['pid']), c['pipe'],
            null_rdev=Path('/dev/null').stat().st_rdev)
        self.p['validate_environment'](self.collector.exec_environment(child['pid']), self.c.env)
        self.c.entry(context, child, image_and_exact_dependency_set_bound=True)
        self.record('entry', snap)

    def wait_call(self):
        self.context(thread=self.init_thread)
        c = self.c.current
        need(c is not None and len(c['children']) >= 1 and self.wait_capture is None
             and not self.wait_observed and self.reg('rdi') == c['children'][0]['identity']['pid']
             and self.reg('rdx') == 0 and self.reg('rsi') > 0,
             'gpgme_parent_wait_arguments')
        self.wait_capture = (self.reg('rdi'), self.reg('rsi'), self.tid())

    def wait_return(self):
        context, snap = self.context(thread=self.init_thread)
        need(self.wait_capture is not None and self.tid() == self.wait_capture[2]
             and self.signed('rax') == self.wait_capture[0]
             and int.from_bytes(self.memory(self.wait_capture[1], 4), 'little') == 0,
             'gpgme_parent_wait_nonzero_error_or_unknown')
        self.wait_observed, self.wait_capture = True, None
        self.flush_exits(context, snap)
        self.refresh_reparent(context, snap)

    def spawn_return(self):
        context, snap = self.context(thread=self.init_thread)
        self.flush_exits(context, snap)
        self.refresh_reparent(context, snap)
        need(self.wait_observed, 'gpgme_parent_wait_not_observed')
        self.c.spawn_return(context, self.tid(), self.signed('rax'))
        need(not (Path('/proc') / str(self.original()['pid']) / 'fd' / str(self.write_fd)).exists(),
             'gpgme_parent_writer_not_closed_by_spawn')
        self.record('spawn_return', snap)

    def read_call(self):
        context, snap = self.context(thread=self.init_thread)
        self.flush_exits(context, snap)
        c = self.c.current
        need(c is not None and c['spawn_returned'] and self.read is None
             and self.tid() == c['thread'], 'gpgme_unmatched_read_call')
        fd, pointer, count = self.reg('rdi'), self.reg('rsi'), self.reg('rdx')
        maximum = 1023 if c['branch'] in self.p['BRANCHES'][:2] else 79
        need(fd == self.pipe_fd and pointer > 0 and 0 < count <= maximum,
             'gpgme_read_source_buffer_or_FD')
        actual = self.collector.fd(self.original()['pid'], fd)
        need(self.p['pipe_identity'](actual, access=0) == c['pipe'], 'gpgme_read_pipe_changed')
        self.read = {'fd': fd, 'pointer': pointer, 'count': count, 'thread': self.tid()}

    def read_return(self):
        context, snap = self.context(thread=self.init_thread)
        self.flush_exits(context, snap)
        need(self.read is not None and self.read['thread'] == self.tid(), 'gpgme_read_return_unmatched')
        value = self.signed('rax')
        need(0 <= value <= self.read['count'], 'gpgme_read_error_or_overrun')
        if value == 0:
            self.read_terminal = 'OBSERVED_READ_EOF'
        elif self.c.current['branch'] in self.p['BRANCHES'][:2]:
            # Successful full buffers/newline parsing are never converted to EOF.
            need(value < 1023 or self.read['count'] < 1023, 'gpgme_discovery_full_buffer_unsupported')
        self.read = None

    def newline_return(self):
        # Exact strchr(buf + oldlen, '\n') result, observed before its branch.
        # It proves the source's newline decision, not read()==0 or empty stdout.
        self.context(thread=self.init_thread)
        need(self.c.current is not None and self.c.current['branch'] in self.p['VERSIONS'],
             'gpgme_newline_wrong_branch')
        if self.reg('rax') != 0:
            self.read_terminal = 'OBSERVED_NEWLINE_THEN_READ_CLOSE'

    def close_call(self):
        self.context(thread=self.init_thread)
        name = self.close_site(at_return=False)
        c = self.c.current
        need(c is not None and self.close_capture is None and self.reg('rdi') == self.pipe_fd
             and self.read is None and self.read_terminal is not None
             and not c['parent_read_closed'], 'gpgme_read_close_without_terminal')
        if name == 'dirs_close_call':
            need(c['branch'] in self.p['BRANCHES'][:2] and self.version_call is None,
                 'gpgme_read_close_wrong_source_route')
        else:
            call = self.version_frame()
            need(c['branch'] == call['route'] and call['spawned'] and not call['read_closed']
                 and not call['null_file'], 'gpgme_read_close_wrong_source_route')
        terminal = ('OBSERVED_NEWLINE_THEN_READ_CLOSE' if name == 'version_newline_close_call'
                    else 'OBSERVED_READ_EOF')
        need(self.read_terminal == terminal, 'gpgme_read_close_terminal_route')
        actual = self.collector.fd(self.original()['pid'], self.pipe_fd)
        need(self.p['pipe_identity'](actual, access=0) == c['pipe'], 'gpgme_close_pipe_changed')
        self.close_capture = {'return_site': name.replace('_call', '_return'),
            'thread': self.tid(), 'stack': self.reg('rsp'), 'frame': self.reg('rbp'),
            'fd': self.pipe_fd, 'pipe': copy.deepcopy(c['pipe']), 'invocation': c,
            'terminal': self.read_terminal}

    def close_site(self, *, at_return):
        suffix = '_return' if at_return else '_call'
        names = [family + suffix for family in
                 ('dirs_close', 'version_close', 'version_newline_close')]
        pc = int(self.g.newest_frame().pc())
        found = [name for name in names if pc == self.binding['load_bias'] + SITE_OFFSETS[name]]
        need(len(found) == 1, 'gpgme_close_unknown_source_site')
        self.site(found[0])
        return found[0]

    def close_return(self):
        context, snap = self.context(thread=self.init_thread)
        name = self.close_site(at_return=True)
        capture = self.close_capture
        if capture is None:
            # 0x42beb is also the common NULL epilogue: null file, failed
            # pipe/spawn, and parser failures can jump here without close().
            # Only the proven no-spawn or already-closed version call may do
            # so; never infer read closure from this PC or inspect stale FDs.
            need(name == 'version_close_return', 'gpgme_read_close_return_unmatched')
            call = self.version_frame()
            need(not call['null_epilogue'] and self.c.current is None and self.read is None
                 and self.pipe_fd is None and self.write_fd is None and self.read_terminal is None,
                 'gpgme_version_null_epilogue_unclosed')
            need((call['null_file'] and not call['spawned'] and not call['read_closed'])
                 or (not call['null_file'] and call['spawned'] and call['read_closed']),
                 'gpgme_version_epilogue_without_spawn_or_close')
            call['null_epilogue'] = True
            return
        need(name == capture['return_site'] and self.tid() == capture['thread']
             and self.reg('rsp') == capture['stack'] and self.reg('rbp') == capture['frame']
             and self.c.current is capture['invocation'] and self.pipe_fd == capture['fd']
             and self.c.current['pipe'] == capture['pipe']
             and self.read is None and self.read_terminal == capture['terminal'],
             'gpgme_read_close_return_unmatched')
        if name != 'dirs_close_return':
            call = self.version_frame()
            need(call['spawned'] and not call['read_closed'] and not call['null_file'],
                 'gpgme_version_read_close_duplicate')
        self.flush_exits(context, snap)
        self.refresh_reparent(context, snap)
        need(self.signed('rax') == 0 and not
             (Path('/proc') / str(self.original()['pid']) / 'fd' / str(self.pipe_fd)).exists(),
             'gpgme_read_close_not_observed_absent')
        self.close_capture = None
        if name != 'dirs_close_return':
            self.version_call['read_closed'] = True
            self.version_call['null_epilogue'] = name == 'version_close_return'
        self.c.pipe_terminal(context, self.tid(), self.c.current['pipe'],
            read_closed=True, terminal=self.read_terminal)
        self.record('pipe_terminal', snap)
        if not self.try_close(context, snap):
            self.pending = 'GPG_DRAIN'

    def flush_exits(self, context, snap):
        if self.c is None or self.c.current is None:
            return
        c = self.c.current
        for index, child in enumerate(c['children']):
            inf = child['inferior']
            absent = not (Path('/proc') / str(child['identity']['pid'])).exists()
            if child['exit_code'] is None and inf in self.exits:
                if index == 1:
                    first_inf = c['children'][0]['inferior']
                    if (first_inf in self.exit_order and self.exit_order.index(first_inf) <
                            self.exit_order.index(inf)):
                        need(child['identity']['ppid'] == self.collector.reaper['pid'],
                             'gpgme_reparent_transition_unobserved_before_final_exit')
                self.c.exit(context, child['identity'], inf, self.exits.pop(inf), absent=absent)
                self.record('exit' + str(index + 1), snap)
            elif child['exit_code'] == 0 and not child['absent'] and absent:
                self.c.observe_absence(context, child['identity'], inf)

    def try_close(self, context, snap):
        c = self.c.current
        if (c is None or not c['parent_read_closed'] or len(c['children']) != 2
                or not all(v['absent'] and v['exit_code'] == 0 for v in c['children'])):
            return False
        self.collector.no_pipe_writer_or_descendant(c['pipe'], [v['identity'] for v in c['children']])
        need(not (Path('/proc') / str(self.original()['pid']) / 'fd' / str(self.pipe_fd)).exists(),
             'gpgme_parent_read_FD_reappeared')
        self.record('close', snap)
        observations = copy.deepcopy(self.observations)
        self.c.close_invocation(context, no_writer_or_other_descendant=True, pipe_read_end_absent=True)
        self.c.invocations[-1]['observations'] = observations
        # Clone entries authorize this closed double-fork only. The original
        # PID and first-fork source offset recur in the next engine branch.
        # Retire them after actual exit/absence/pipe closure, never mid-flight.
        self.clone_entries.clear()
        self.caller_route = self.caller_thread = None
        self.pipe_fd = self.write_fd = self.read_terminal = None
        return True

    def engine_return(self):
        if not self.init_active:
            call = self.cached_call
            need(self.finished_initialization and call is not None
                 and self.g.selected_inferior().num == 1 and self.tid() == call['thread']
                 and self.reg('rsp') == call['stack'] and self.signed('rax') == 0
                 and self.version_call is None and self.close_capture is None,
                 'gpgme_cached_engine_return_unmatched')
            self.context(thread=call['thread'])
            self.cached_call = None
            return
        context, snap = self.context(thread=self.init_thread)
        self.flush_exits(context, snap)
        self.refresh_reparent(context, snap)
        need(self.tid() == self.init_thread and self.reg('rsp') == self.init_stack
             and self.signed('rax') == 0 and self.version_call is None
             and self.close_capture is None, 'gpgme_engine_return_identity_status_stack')
        self.finished_at_return = True
        self.try_close(context, snap)
        if self.c.current is not None:
            self.pending = 'GPG_DRAIN'
        else:
            self.finish(context)

    def finish(self, context):
        need(self.finished_at_return and self.version_call is None and self.close_capture is None
             and self.cached_call is None, 'gpgme_finish_before_exact_return')
        self.c.finish_initialization(context, exact_engine_info_return=True, known_no_more_spawn=True)
        self.init_active, self.finished_initialization = False, True
        self.retire_process_guards()
        self.pending = 'CONTINUE'

    def boundary(self, event):
        need(self.n['STATE']['error'] is None and self.fork_pending is None,
             'gpgme_pending_fork_terminal_or_reentry')
        need(self.init_active, 'gpgme_unexpected_fork_vfork_exec_outside_initialization')
        kind = self.guard_kind(event)
        if kind == 'fork':
            self.capture_fork()
            return
        elif kind == 'exec':
            self.exec_stop()
        elif kind == 'clone_guard':
            self.clone_guard()
        elif kind == 'exit_intent':
            self.exit_intent()
        else:
            raise RuntimeError('gpgme_unsupported_process_or_session_event')
        self.pending = 'CONTINUE'

    def queue_stop(self, event):
        hits = [b for b in getattr(event, 'breakpoints', ()) if b.number in self.owned_numbers()]
        if not hits:
            return False
        need(len(hits) == len(event.breakpoints) == 1 and self.pending_stop is None,
             'gpgme_ambiguous_or_duplicate_breakpoint_event')
        bp = hits[0]
        need(bp.number not in self.retired and bp.is_valid() and bp.enabled,
             'gpgme_retired_or_disabled_breakpoint_event')
        inf = self.g.selected_inferior()
        need(inf.num == bp.inferior and inf.pid > 0, 'gpgme_breakpoint_event_inferior')
        self.pending_stop = (bp.number, inf.num, inf.pid, self.tid(), int(self.g.newest_frame().pc()))
        return True

    def clone_guard(self):
        # glibc fork uses clone(SIGCHLD|CHILD_SETTID|CHILD_CLEARTID) on the
        # exact pinned x86-64 libc. No CLONE_VM/THREAD or generic clone grant.
        need(self.reg('orig_rax') == 56 and self.c is not None and self.c.current is not None,
             'gpgme_unsupported_clone_syscall')
        context, snap = self.context(role='fork_syscall')
        pc = int(self.g.newest_frame().pc())
        libc = self.collector.image_binding(self.g.selected_inferior().pid,
            self.m['collector_pins']['libc'], pc)
        need(libc['relative_pc'] == LIBC_FORK_SYSCALL_RETURN
             and self.memory(pc - 2, 10).hex() == LIBC_FORK_SYSCALL_BYTES
             and self.reg('rsi') == self.reg('rdx') == self.reg('r8') == 0
             and self.reg('r10') > 0, 'gpgme_clone_exact_libc_syscall_site')
        c = self.c.current
        frame = self.g.newest_frame()
        offsets = []
        for _ in range(24):
            if frame is None or not frame.is_valid():
                break
            offsets.append(int(frame.pc()) - self.binding['load_bias'])
            frame = frame.older()
        candidates = [v for v in (self.p['FIRST_FORK_RETURN'], self.p['SECOND_FORK_RETURN']) if v in offsets]
        need(len(candidates) == 1, 'gpgme_clone_exact_fork_source')
        offset, pid, tid = candidates[0], self.g.selected_inferior().pid, self.tid()
        source_index = 0 if offset == self.p['FIRST_FORK_RETURN'] else 1
        expected_parent = self.original() if source_index == 0 else c['children'][0]['identity']
        value = self.signed('rax', 64)
        if value == -38:  # actual Linux ptrace syscall-entry RAX = -ENOSYS
            need(pid == expected_parent['pid'] and self.reg('rdi') == 0x1200011
                 and tid == (c['thread'] if source_index == 0 else [pid, pid, 0])
                 and (pid, offset) not in self.clone_entries, 'gpgme_clone_fork_flags_or_thread')
            self.clone_entries.add((pid, offset))
        else:
            need(value >= 0 and (expected_parent['pid'], offset) in self.clone_entries,
                 'gpgme_clone_return_without_exact_entry')
            child = c['children'][source_index] if len(c['children']) > source_index else None
            need(child is not None and ((pid == expected_parent['pid'] and value == child['identity']['pid'])
                 or (pid == child['identity']['pid'] and value == 0)), 'gpgme_clone_return_identity')

    def exit_intent(self):
        # Observe actual PPID/birth BEFORE the task disappears, including the
        # final child's real reparent. A later GDB exit event must still give0.
        inf = self.g.selected_inferior()
        need(self.c is not None and self.c.current is not None and inf.num > 3
             and self.exit_completion is None and inf.num not in self.exit_intents
             and self.reg('rdi') == 0,
             'gpgme_unknown_duplicate_or_nonzero_exit_intent')
        context, snap = self.context(role='exiting_child')
        self.flush_exits(context, snap)
        self.refresh_reparent(context, snap)
        child = self.collector.proc(inf.pid)
        c = self.c.current
        if len(c['children']) == 2 and inf.num == c['children'][1]['inferior']:
            image = self.m['helpers'][c['role']]
            self.collector.exec_image(inf.pid, image, [image['path'], self.p['OPTIONS'][c['branch']]])
            self.p['validate_exec_fds'](self.collector.fds(inf.pid), c['pipe'],
                null_rdev=Path('/dev/null').stat().st_rdev)
            self.p['validate_environment'](self.collector.exec_environment(inf.pid), self.c.env)
            self.collector.dependencies(inf.pid, c['role'], entry=True,
                phase='exit_intent', branch=c['branch'])
        matches = [v for v in self.c.current['children'] if v['inferior'] == inf.num]
        need(len(matches) == 1 and matches[0]['identity'] == child,
             'gpgme_exit_intent_actual_identity')
        self.exit_intents[inf.num] = copy.deepcopy(child)
        # Do not resume the original with this child disappearing in parallel.
        # GNU17.1 may defer its ExitedEvent behind another inferior's stop.
        # Dispatch completes exactly this syscall before ordinary read-return.
        self.exit_completion = dict(inferior=inf.num, identity=copy.deepcopy(child),
                                    selected=self._selection(), attempted=False)

    def complete_exit_intent(self):
        """One sole-child completion, outside callbacks, on the existing clock.

        The normal synchronous GNU17.1 all-stop command boundary clears the
        global step-over queue and resumed intents (same source proof as drain).
        Settings alone do not establish that proof. No absence substitutes for
        the actual zero ExitedEvent. A refusal never retries this command.
        """
        token = self.exit_completion
        need(type(token) is dict and not token['attempted']
             and self.n['STATE'].get('helper_event_depth', 0) == 0
             and self.n['STATE']['error'] is None and self.init_active
             and self.fork_pending is None and self.pending_stop is None
             and not self.to_create and not self.to_retire,
             'gpgme_exit_completion_unavailable')
        need(self._selection() == token['selected']
             and self.collector.proc(token['identity']['pid']) == token['identity']
             and token['inferior'] in self.exit_intents
             and self.exit_intents[token['inferior']] == token['identity'],
             'gpgme_exit_completion_custody_changed')
        settings = {key: self.g.parameter(key) for key in
                    ('follow-fork-mode', 'schedule-multiple', 'scheduler-locking')}
        # During the existing held-original drain the sole-child settings
        # already hold; otherwise require the unchanged launch baseline.
        baseline = {'follow-fork-mode': 'parent', 'schedule-multiple': True,
                    'scheduler-locking': 'off'}
        sole = {'follow-fork-mode': 'parent', 'schedule-multiple': False,
                'scheduler-locking': 'on'}
        need(settings == (sole if self.n['STATE'].get('gpgme_drain_active', False) else baseline),
             'gpgme_exit_completion_runcontrol_changed')
        need(self.paper.original_selected(thread=self.init_thread),
             'gpgme_exit_completion_original_unavailable')
        held = self._selection()
        failure = None
        prior_drain = self.n['STATE'].get('gpgme_drain_active', False)
        self.n['STATE']['gpgme_drain_active'] = True
        token['attempted'] = True
        try:
            self.context(thread=self.init_thread)
            self._restore_selection(token['selected'])
            self.context(role='exiting_child')
            for key, value in (('schedule-multiple', 'off'), ('scheduler-locking', 'on')):
                self.g.execute('set ' + key + ' ' + value, to_string=True)
            need({key: self.g.parameter(key) for key in sole} == sole,
                 'gpgme_exit_completion_runcontrol_readback')
            self.context(role='exiting_child')
            self.g.execute('continue', to_string=True)
            need(self.n['STATE']['error'] is None and self.pending_stop is None
                 and self.fork_pending is None and self.exit_completion is token
                 and self.exits.get(token['inferior']) == 0
                 and token['inferior'] in self.process_guard_retire_queue,
                 'gpgme_exit_completion_actual_event_missing')
            need(not any(i.is_valid() and i.num == token['inferior'] and i.pid
                         for i in self.g.inferiors()),
                 'gpgme_exit_completion_debugger_not_retired')
            self._restore_selection(held)
            self.context(thread=self.init_thread)
            self.exit_completion = None
        except Exception as exc:
            failure = exc
        finally:
            self.n['STATE']['gpgme_drain_active'] = prior_drain
            for key, value in settings.items():
                try:
                    text = ('on' if value else 'off') if type(value) is bool else value
                    self.g.execute('set ' + key + ' ' + text, to_string=True)
                    need(self.g.parameter(key) == value, 'gpgme_exit_completion_restore_settings')
                except Exception as exc:
                    failure = failure or exc
            try:
                self._restore_selection(held)
            except Exception as exc:
                failure = failure or exc
        if failure is not None:
            self.clear_pending()
            raise failure
        self.pending = 'CONTINUE'

    def exited(self, event):
        inf = getattr(event, 'inferior', None)
        need(inf is not None, 'gpgme_exit_inferior_unknown')
        if inf.num == 1:
            need(self.finished_initialization, 'gpgme_original_exit_before_closed_initialization')
            return False
        matches = [v for v in self.known.values() if v['inferior'] == inf.num]
        need(len(matches) == 1 and inf.num not in self.exits and inf.num in self.exit_intents
             and matches[0]['identity'] == self.exit_intents[inf.num]
             and type(getattr(event, 'exit_code', None)) is int and event.exit_code == 0,
             'gpgme_unknown_duplicate_or_nonzero_exit')
        need(self.process_guard_states.get(inf.num) == 'ACTIVE'
             and inf.num not in self.process_guard_retire_queue, 'gpgme_process_guard_exit_not_enrolled')
        self.process_guard_retire_queue.append(inf.num)
        self.exits[inf.num] = event.exit_code
        self.exit_order.append(inf.num)
        self.pending = 'CONTINUE'
        return True

    def dispatch(self):
        need(self.n['STATE'].get('helper_event_depth', 0) == 0,
             'gpgme_dispatch_inside_event_callback')
        if self.n['STATE']['error'] is not None:
            self.clear_pending()
            return None
        if self.exit_completion is not None:
            self.complete_exit_intent()
        for owner in tuple(self.process_guard_retire_queue):
            self.retire_process_guards(owner)
        if self.fork_pending is not None:
            self.materialize_fork()
        if self.pending_stop is not None:
            number, inferior, pid, tid, pc = self.pending_stop
            self.pending_stop = None
            bp, fn, one_shot = self.handlers[number]
            need((self.g.selected_inferior().num, self.g.selected_inferior().pid,
                 self.tid(), int(self.g.newest_frame().pc())) == (inferior, pid, tid, pc),
                 'gpgme_queued_stop_context_changed')
            need(bp.is_valid() and bp.enabled, 'gpgme_queued_stop_breakpoint_changed')
            fn()
            if one_shot:
                self.to_retire.append(number)
            self.pending = self.pending or 'CONTINUE'
        if self.init_active:
            originals = [i for i in self.g.inferiors() if i.is_valid() and i.num == 1 and i.pid > 0]
            need(len(originals) == 1, 'gpgme_process_guard_original_unavailable')
            self.enroll_process_guards(originals[0])
        if self.finished_initialization and self.process_guards:
            self.retire_process_guards()
        for number in self.to_retire:
            bp, _fn, _one_shot = self.handlers.pop(number)
            bp.delete()
            need(not bp.is_valid(), 'gpgme_breakpoint_retirement_failed')
            self.breakpoints.remove(bp)
            self.retired.add(number)
        self.to_retire.clear()
        for address, fn, inferior, one_shot in self.to_create:
            self.breakpoint(address, fn, inferior, one_shot)
        self.to_create.clear()
        if self.exits and self.c is not None and self.c.current is not None:
            # Exit events may leave no selected live LWP.  Otherwise preserve
            # the stop's exact thread/frame while observing original custody.
            saved = self._selection() if self.g.selected_inferior().pid else None
            try:
                need(self.paper.original_selected(thread=self.init_thread),
                     'gpgme_exit_original_unavailable')
                context, snap = self.context(thread=self.init_thread)
                self.flush_exits(context, snap)
                self.refresh_reparent(context, snap)
                self.try_close(context, snap)
            finally:
                if saved is not None:
                    self._restore_selection(saved)
        action, self.pending = self.pending, None
        self.publish()
        return action

    def drain(self):
        """Complete this invocation while its exact original LWP stays held.

        A read-close return is an internal library boundary; engine_return is
        the final API boundary.  Both retain the original's exact stopped PC
        until this invocation closes, and only final return may finish init.

        The pinned GNU17.1 ordinary synchronous command path (not a callback
        or hook) clears nonexecuting threads from the GLOBAL step-over queue
        at normal_stop, and native all-stop clears LWP resumed intent.  Fresh
        collector OS+GDB all-stop checks preserve those preconditions.  The
        schedule/locking settings alone are not a sole-child execution proof.
        """
        need(self.n['STATE'].get('helper_event_depth', 0) == 0,
             'gpgme_drain_inside_event_callback')
        need(self.init_active and self.c.current is not None
             and self.c.current['parent_read_closed'], 'gpgme_drain_wrong_phase')
        need(self.paper.original_selected(thread=self.init_thread), 'gpgme_drain_original_unavailable')
        held = self._selection()
        need(list(held[2]) == self.init_thread, 'gpgme_drain_original_thread_changed')
        settings = {key: self.g.parameter(key) for key in
                    ('follow-fork-mode', 'schedule-multiple', 'scheduler-locking')}
        need(settings == {'follow-fork-mode': 'parent', 'schedule-multiple': True,
                          'scheduler-locking': 'off'}, 'gpgme_drain_runcontrol_changed')
        failure = None
        need(not self.n['STATE'].get('gpgme_drain_active', False), 'gpgme_drain_reentry')
        self.n['STATE']['gpgme_drain_active'] = True
        try:
            while self.c.current is not None:
                need(self.n['STATE']['error'] is None and self.fork_pending is None
                     and self.pending_stop is None and not self.to_create and not self.to_retire,
                     'gpgme_drain_pending_or_refused')
                self._restore_selection(held)
                context, snap = self.context(thread=self.init_thread)
                self.flush_exits(context, snap)
                self.refresh_reparent(context, snap)
                if self.c.current is None or self.try_close(context, snap):
                    break
                c = self.c.current
                numbers = {v['inferior'] for v in c['children']}
                live = [i for i in self.g.inferiors() if i.is_valid() and i.pid and i.num in numbers]
                need(len(live) <= 2, 'gpgme_drain_unknown_children')
                if live:
                    # Select the final live child first; fall back to its
                    # original intermediate only while it remains observed.
                    child = max(live, key=lambda i: i.num)
                    threads = list(child.threads())
                    need(len(threads) == 1 and threads[0].is_valid() and threads[0].is_stopped()
                         and list(threads[0].ptid) == [child.pid, child.pid, 0],
                         'gpgme_drain_child_thread_changed')
                    threads[0].switch()
                    self.context(role='final' if child.num == c['children'][-1]['inferior'] else 'intermediate')
                    for key, value in (('schedule-multiple', 'off'), ('scheduler-locking', 'on')):
                        self.g.execute('set ' + key + ' ' + value, to_string=True)
                    need(self.g.parameter('follow-fork-mode') == 'parent'
                         and self.g.parameter('schedule-multiple') is False
                         and self.g.parameter('scheduler-locking') == 'on',
                         'gpgme_drain_runcontrol_readback')
                    # All-stop + exact source induction closes both the global
                    # step-over queue and native async wait-resume edges.
                    self.context(role='final' if child.num == c['children'][-1]['inferior'] else 'intermediate')
                    self.g.execute('continue', to_string=True)
                    need(self.n['STATE']['error'] is None, 'gpgme_drain_refused')
                    # Save this stop before checking the held original.  A
                    # queued breakpoint handler belongs to the event LWP.
                    event_selection = self._selection() if self.g.selected_inferior().pid else None
                    # Refuse an unfinished asynchronous continue before
                    # dispatch/another resume, without asking for running frames.
                    self._restore_selection(held)
                    self.context(thread=self.init_thread)
                    if event_selection is not None:
                        self._restore_selection(event_selection)
                    action = self.dispatch()
                    need(action == 'CONTINUE', 'gpgme_drain_unrecognized_stop')
                else:
                    need(all(child['exit_code'] == 0 for child in c['children']),
                         'gpgme_exit_status_unknown_at_reap_boundary')
                    # Only the already-observed reaper may remove these exited
                    # PIDs.  No actor resumes and no fresh clock is created.
                    time.sleep(min(0.005, max(0, self.b['runtime']['operation_deadline_monotonic'] - time.monotonic())))
        except Exception as exc:
            failure = str(exc) if type(exc) is RuntimeError else type(exc).__name__
        finally:
            self.n['STATE']['gpgme_drain_active'] = False
            # Bounded nonexecuting restoration also runs after the first error.
            for key, value in settings.items():
                try:
                    text = ('on' if value else 'off') if type(value) is bool else value
                    self.g.execute('set ' + key + ' ' + text, to_string=True)
                    need(self.g.parameter(key) == value, 'gpgme_drain_restore_settings')
                except Exception as exc:
                    failure = failure or (str(exc) if type(exc) is RuntimeError else type(exc).__name__)
            try:
                self._restore_selection(held)
            except Exception as exc:
                failure = failure or (str(exc) if type(exc) is RuntimeError else type(exc).__name__)
        if failure is not None:
            self.clear_pending()
            raise RuntimeError(failure)
        context, _snap = self.context(thread=self.init_thread)
        if self.finished_at_return:
            self.finish(context)
        else:
            self.pending = 'CONTINUE'
        self.publish()

    def identity_scope(self):
        for inf in self.g.inferiors():
            if not inf.pid or inf.num == 1:
                continue
            known = self.known.get(inf.pid)
            need(known is not None and known['inferior'] == inf.num,
                 'gpgme_foreign_live_inferior')
            actual = self.collector.proc(inf.pid)
            need(actual == known['identity'], 'gpgme_live_inferior_birth_or_parent')
        return True

    def metric_ready(self):
        need(self.finished_initialization and self.c is not None and self.c.closed
             and self.c.current is None and not self.exits, 'gpgme_not_closed_before_metric')
        self.paper_closed()
        need(all(not (Path('/proc') / str(pid)).exists() for pid in self.known),
             'gpgme_child_present_before_metric')

    def clear_pending(self):
        if self.fork_pending is not None:
            self.fork_terminal = True
        self.fork_pending = None
        self.exit_completion = None
        self.pending = self.pending_stop = None
        self.to_create.clear()
        self.to_retire.clear()

    def snapshot(self):
        invocations = [] if self.c is None else self.c.snapshot()['invocations']
        return {'schema': 'frw.calc.gpgme-engine-init-evidence.v2',
            'status': 'REFUSED' if self.n['STATE']['error'] else
                ('CLOSED' if self.finished_initialization else 'UNRELEASED'),
            'runtime': copy.deepcopy(self.b['runtime']),
            'original': None if self.c is None else copy.deepcopy(self.c.original),
            'reaper': copy.deepcopy(self.collector.reaper),
            'invocations': invocations, 'first_refusal': self.n['STATE']['error'],
            'actual_M': None, 'runtime_attested': False}

    def publish(self):
        value = self.snapshot()
        self.n['STATE']['gpgme_engine_init'] = value
        raw = (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()
        need(len(raw) <= 262144, 'gpgme_evidence_bound')
        path = Path(self.b['evidence_path'])
        # Fixed file in the private observer output directory.  No release
        # marker or metric is emitted by this adapter.
        temp = path.with_name(path.name + '.pending')
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        with os.fdopen(fd, 'wb') as out:
            out.write(raw)
            out.flush()
            os.fsync(out.fileno())
        if path.exists():
            st = path.lstat()
            need(stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid() and st.st_nlink == 1
                 and stat.S_IMODE(st.st_mode) == 0o600, 'gpgme_evidence_current_rights')
        os.replace(temp, path)
        self.n['save']()


class MultiCustody:
    """Disjoint event ownership.  Paper semantics and numbering stay exact."""
    def __init__(self, paper, gpgme):
        self.paper, self.gpgme = paper, gpgme

    def __getattr__(self, name):
        return getattr(self.paper, name)

    def original_selected(self):
        # Both actual callers use this union entry after a child exit.
        # Keep the initialized worker, not paper's already-closed default LWP.
        thread = self.gpgme.init_thread if self.gpgme.init_active else None
        return self.paper.original_selected(thread=thread)

    def install(self):
        self.paper.install()
        self.gpgme.install()

    def materialization_stop(self, event):
        if self.gpgme.fork_pending is None:
            return False
        need(self.paper.pending is None and self.paper.pending_stop is None,
             'gpgme_pending_fork_paper_collision')
        return self.gpgme.materialization_stop(event)

    def queue_stop(self, event):
        numbers = {b.number for b in getattr(event, 'breakpoints', ())}
        paper = set(self.paper.stop_handlers) | self.paper.retired_breakpoints
        gpgme = self.gpgme.owned_numbers()
        need(not paper & gpgme, 'gpgme_breakpoint_owner_collision')
        need(not (numbers & paper and numbers & gpgme), 'gpgme_multi_custody_ambiguous_event')
        if numbers & gpgme:
            return self.gpgme.queue_stop(event)
        if numbers & paper:
            need(not self.gpgme.init_active, 'gpgme_paper_event_during_engine_initialization')
            return self.paper.queue_stop(event)
        return False

    def boundary(self, event):
        if self.gpgme.init_active or self.gpgme.finished_initialization:
            return self.gpgme.boundary(event)
        return self.paper.boundary(event)

    def exited(self, event):
        inf = getattr(event, 'inferior', None)
        need(inf is not None, 'gpgme_union_exit_inferior_unknown')
        paper_numbers = set() if self.paper.c is None else {
            c['inferior'] for c in self.paper.c.e['children']}
        gpgme_numbers = {v['inferior'] for v in self.gpgme.known.values()}
        need(not paper_numbers & gpgme_numbers, 'gpgme_exit_owner_collision')
        if inf.num == 1:
            self.gpgme.metric_ready()
            return self.paper.exited(event)
        if inf.num in paper_numbers:
            return self.paper.exited(event)
        need(inf.num in gpgme_numbers, 'gpgme_union_foreign_exit')
        return self.gpgme.exited(event)

    def dispatch(self):
        a, b = self.paper.dispatch(), self.gpgme.dispatch()
        need(a is None or b is None, 'gpgme_multi_custody_dispatch_collision')
        return a or b

    def metric_ready(self):
        self.paper.metric_ready()
        self.gpgme.metric_ready()

    def identity_scope(self):
        paper_pids = self.paper.known
        gpgme_pids = self.gpgme.known
        need(not set(paper_pids) & set(gpgme_pids), 'gpgme_process_owner_collision')
        for inf in self.paper.g.inferiors():
            if not inf.pid or inf.num == 1:
                continue
            if inf.pid in paper_pids:
                need(self.paper.c.e['state'] != 'CLOSED'
                     and self.paper.proc(inf.pid) == paper_pids[inf.pid], 'gpgme_paper_live_identity')
            else:
                known = gpgme_pids.get(inf.pid)
                need(known is not None and known['inferior'] == inf.num
                     and self.gpgme.collector.proc(inf.pid) == known['identity'],
                     'gpgme_union_foreign_live_inferior')
        return True

    def clear_pending(self):
        self.paper.pending = self.paper.pending_stop = None
        self.paper.to_create.clear()
        self.gpgme.clear_pending()

    def cleanup_identity(self, inferior):
        """Read-only birth CAS for native finally, even after collector refusal.

        Terminal observation state is never reset. The raw paper parser is
        used solely against the disjoint, previously accepted launch registry.
        Unknown inferiors and vanished processes confer no kill permission.
        """
        need(inferior.is_valid() and type(inferior.pid) is int and inferior.pid > 0,
             'gpgme_cleanup_inferior_unknown')
        pid = inferior.pid
        native = self.paper.n['STATE']['process']
        if inferior.num == 1:
            need(native is not None and pid == native['pid'], 'gpgme_cleanup_original_unknown')
            expected = dict(pid=pid, ppid=native['gdb_pid'], start_ticks=native['start_ticks'])
        elif pid in self.paper.known:
            matches = [] if self.paper.c is None else [v for v in self.paper.c.e['children']
                if v['pid'] == pid and v['inferior'] == inferior.num]
            need(len(matches) == 1 and self.paper.c.e['state'] != 'CLOSED',
                 'gpgme_cleanup_paper_owner_unknown')
            expected = self.paper.known[pid]
        else:
            known = self.gpgme.known.get(pid)
            need(known is not None and known['inferior'] == inferior.num,
                 'gpgme_cleanup_foreign_inferior')
            expected = known['identity']
        actual = self.paper.proc(pid)
        need(actual == expected, 'gpgme_cleanup_birth_or_parent_changed')
        return actual

    def cleanup_inferiors(self):
        # Cleanup is the native launch owner's operation, never an adapter's
        # permission to kill a foreign process.  Preserve the first refusal.
        self.clear_pending()
        self.paper.cleanup_inferiors()
