"""Inert source component for Root review. No native imports or target invocation.

Only local PY_START/PY_RETURN. CPython 3.14 PY_UNWIND is not local, so
raised counts are unavailable. Terminal class is an outer host observation;
unfinished spans are explicitly unresolved, never inferred as raised.
A separate Root host must own genuine graph setup, readonly fences, CPU/wall
limits, source/callable authentication, and output. This is not that host.
"""
import sys
import time
import types
import threading

LABELS = frozenset(("continuation_key", "serial_history_guard",
                    "retired_prepared", "prepared_unsent"))


class ExactLocalCounters:
    def __init__(self, exact_codes, exact_callers, *, lifetime_id=1, tool_id=5):
        if (type(exact_codes) is not dict or set(exact_codes) != LABELS
                or any(type(code) is not types.CodeType or code.co_name != label
                       or code.co_flags & (0x20 | 0x80 | 0x200)
                       for label, code in exact_codes.items())
                or len(set(exact_codes.values())) != 4
                or type(lifetime_id) is not int or lifetime_id < 1
                or tool_id not in (3, 4, 5)):
            raise ValueError("exact_four_non_generator_code_objects_required")
        categories = {"prepared_unsent": 1, "prepared_claim_pin": 2,
                      "prepared_absent_claim_pin": 3}
        if (type(exact_callers) is not dict or set(exact_callers) != set(categories)
                or any(type(code) is not types.CodeType or code.co_name != label
                       for label, code in exact_callers.items())):
            raise ValueError("exact_three_native_key_callers_required")
        self.codes = {id(code): (code, label) for label, code in exact_codes.items()}
        self.callers = {id(code): (code, categories[label])
                        for label, code in exact_callers.items()}
        self.callsites = {}
        self.callsite_overflow = 0
        self.owner_thread = None
        self.lifetime_id = lifetime_id
        self.tool_id = tool_id
        self.name = "frw-r27-exact-local-retired-counts-" + str(time.monotonic_ns())
        self.active = {}
        self.rows = {label: dict(entered=0, completed=0, raised=None,
            max_selected_depth=0, completed_inclusive_wall_seconds=0.0,
            completed_inclusive_cpu_seconds=0.0,
            unresolved_frame_identity_reuse=0) for label in LABELS}
        self.started = False
        self.observer_refused = False
        self.cleanup_confirmed = False
        self.start_wall = self.start_cpu = None
        self.end_wall = self.end_cpu = None

    def _frame_key(self, code):
        frame = sys._getframe(2)
        # CPython 3.14 callback's caller is the monitored frame. Root's inert
        # selected-interpreter control must qualify this before real use.
        if frame.f_code is not code:
            self.observer_refused = True
            raise RuntimeError("selected_interpreter_callback_frame_mismatch")
        if threading.get_ident() != self.owner_thread:
            self.observer_refused = True
            raise RuntimeError("single_diagnostic_thread_required")
        key = id(frame)
        callsite = None
        if code.co_name == "continuation_key":
            caller = frame.f_back
            if caller is None:
                callsite = (0, -1)
            else:
                entry = self.callers.get(id(caller.f_code))
                category = entry[1] if entry is not None and entry[0] is caller.f_code else 0
                callsite = (category, caller.f_lasti)
            del caller
        depth = 0
        while frame is not None:
            entry = self.codes.get(id(frame.f_code))
            if entry is not None and entry[0] is frame.f_code:
                depth += 1
            frame = frame.f_back
        return key, depth, callsite

    def _start(self, code, offset):
        entry = self.codes.get(id(code))
        if entry is None or entry[0] is not code:
            self.observer_refused = True
            raise RuntimeError("unexpected_local_code")
        wall, cpu = time.monotonic(), time.process_time()
        key, depth, callsite = self._frame_key(code)
        previous = self.active.pop(key, None)
        if previous is not None:
            # Frame ids may be reused after an unobserved unwind. This is an
            # unresolved old span, not an attributed return or raised count.
            self.rows[previous[0]]["unresolved_frame_identity_reuse"] += 1
        if len(self.active) >= 256:
            self.observer_refused = True
            raise RuntimeError("bounded_selected_span_cap")
        label = entry[1]
        if callsite is not None:
            if callsite not in self.callsites:
                if len(self.callsites) >= 32:
                    self.callsite_overflow += 1
                    callsite = None
                else:
                    self.callsites[callsite] = dict(entered=0, completed=0)
            if callsite is not None:
                self.callsites[callsite]["entered"] += 1
        self.active[key] = (label, code, wall, cpu, callsite)
        row = self.rows[label]
        row["entered"] += 1
        row["max_selected_depth"] = max(row["max_selected_depth"], depth)

    def _return(self, code, offset, value):
        # Return payload is never inspected, retained, serialized, or logged.
        wall, cpu = time.monotonic(), time.process_time()
        key, unused_depth, unused_callsite = self._frame_key(code)
        span = self.active.pop(key, None)
        if span is None or span[1] is not code:
            self.observer_refused = True
            raise RuntimeError("matching_selected_start_required")
        row = self.rows[span[0]]
        row["completed"] += 1
        if span[4] is not None:
            self.callsites[span[4]]["completed"] += 1
        row["completed_inclusive_wall_seconds"] += wall - span[2]
        row["completed_inclusive_cpu_seconds"] += cpu - span[3]

    def __enter__(self):
        if self.started or not hasattr(sys, "monitoring"):
            raise RuntimeError("fresh_supported_monitor_required")
        mon = sys.monitoring
        if mon.get_tool(self.tool_id) is not None:
            raise RuntimeError("monitor_tool_in_use_no_steal")
        mon.use_tool_id(self.tool_id, self.name)
        self.start_wall, self.start_cpu = time.monotonic(), time.process_time()
        self.started = True
        self.owner_thread = threading.get_ident()
        try:
            mon.register_callback(self.tool_id, mon.events.PY_START, self._start)
            mon.register_callback(self.tool_id, mon.events.PY_RETURN, self._return)
            if mon.get_events(self.tool_id) != 0:
                raise RuntimeError("global_events_must_remain_zero")
            for code, label in self.codes.values():
                mon.set_local_events(self.tool_id, code,
                    mon.events.PY_START | mon.events.PY_RETURN)
            return self
        except BaseException:
            try:
                self._stop()
            except BaseException:
                self.observer_refused = True
            raise

    def _stop(self):
        mon = sys.monitoring
        try:
            if mon.get_tool(self.tool_id) != self.name:
                self.observer_refused = True
                raise RuntimeError("monitor_ownership_changed_no_foreign_cleanup")
            # The native CPython3.14 bdb tracer uses clear_tool_id followed by
            # free_tool_id. Never free a still-instrumented dirty slot.
            mon.clear_tool_id(self.tool_id)
            mon.free_tool_id(self.tool_id)
            self.cleanup_confirmed = True
        finally:
            self.end_wall, self.end_cpu = time.monotonic(), time.process_time()

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self._stop()
        except BaseException:
            self.observer_refused = True
            if exc_type is None:
                raise
            # Preserve the original target exception. Root sees the explicit
            # unconfirmed cleanup flag and must reap this diagnostic process.
        return False

    def snapshot(self):
        if not self.started or threading.get_ident() != self.owner_thread:
            raise RuntimeError("started_same_diagnostic_thread_required")
        wall, cpu = time.monotonic(), time.process_time()
        if self.end_wall is not None:
            wall, cpu = self.end_wall, self.end_cpu
        # Determine live selected activations from this thread's actual stack.
        # No frame, code path, locals, values, exception or raw identity escapes.
        live = set()
        frame = sys._getframe(1)
        walked = 0
        while frame is not None:
            walked += 1
            if walked > 2048:
                raise RuntimeError("bounded_snapshot_stack_cap")
            span = self.active.get(id(frame))
            if span is not None and span[1] is frame.f_code:
                live.add(id(frame))
            frame = frame.f_back
        rows = {label: dict(row) for label, row in self.rows.items()}
        for label, row in rows.items():
            pending = [(key, span) for key, span in self.active.items()
                       if span[0] == label]
            active = [span for key, span in pending if key in live]
            row["active_on_current_stack"] = len(active)
            row["unresolved_not_on_current_stack"] = len(pending) - len(active)
            row["active_so_far_inclusive_wall_seconds"] = sum(wall-span[2] for span in active)
            row["active_so_far_inclusive_cpu_seconds"] = sum(cpu-span[3] for span in active)
            row["all_entered_returned"] = (row["entered"] == row["completed"])
        mon = sys.monitoring
        slot_name = mon.get_tool(self.tool_id)
        actual_global_events = mon.get_events(self.tool_id) if slot_name == self.name else None
        return dict(lifetime_id=self.lifetime_id,
            state="IN_PROGRESS" if self.end_wall is None else "CLOSED", rows=rows,
            observer_refused=self.observer_refused,
            cleanup_confirmed=self.cleanup_confirmed,
            interval_wall_seconds=wall-self.start_wall,
            interval_cpu_seconds=cpu-self.start_cpu,
            continuation_key_callsites=[dict(caller_category=key[0], caller_f_lasti=key[1], **row)
                                       for key, row in sorted(self.callsites.items())],
            callsite_overflow=self.callsite_overflow,
            callsite_semantics="Caller frame f_lasti at callee PY_START; CPython bytecode offset, not source line or callee event offset",
            caller_category_semantics="0=aggregate other callers sharing f_lasti;1=exact prepared_unsent;2=exact prepared_claim_pin;3=exact prepared_absent_claim_pin",
            raised_count_supported=False,
            unsupported_event="PY_UNWIND_IS_NONLOCAL_IN_CPYTHON_3_14",
            inclusive_timings_must_not_be_summed=True,
            completed_timings_cover_completed_identified_frames_only=True,
            active_so_far_times_are_separate_partial_spans=True,
            unresolved_span_times_and_raised_counts_are_unmeasured=True,
            CPU_semantics="process_time includes every process thread",
            configured_global_events=0, observed_owned_slot_global_events=actual_global_events,
            target_function_or_code_replacements=0)


if __name__ == "__main__":
    raise SystemExit("NO_RUNNABLE_ENTRY: real retained owner/read-only host boundary required")
