"""DORMANT, metadata-only PyUNO conversion probe. No UNO imports or I/O.

Root must separately admit one fresh private client and one retained readonly
load. This is NOT a compatibility fix or acceptance policy. Original setters
run unchanged and faults are re-raised. No exception/payload values are read.
"""
import re
import types

_UNO_NAME = re.compile(r"com\.sun\.star(?:\.[A-Za-z_][A-Za-z0-9_]*){1,16}\Z")
_BUILTIN_NAME = re.compile(r"builtins\.[A-Za-z_][A-Za-z0-9_]*\Z")
_SOURCE_NAMES = frozenset(("conversion_probe.py", "callback_observer_v2.py",
                           "readonly_diagnostic.py", "uno.py"))
_COMPAT_NAMES = (
    "com.sun.star.task.DocumentPasswordRequest",
    "com.sun.star.task.DocumentMSPasswordRequest",
    "com.sun.star.task.DocumentPasswordRequest2",
    "com.sun.star.task.DocumentMSPasswordRequest2",
    "com.sun.star.task.ErrorCodeRequest2",
)


class ProbeRefused(RuntimeError):
    pass


def _class_dict(cls):
    return type.__getattribute__(cls, "__dict__")


def _uno_name(cls):
    name = _class_dict(cls).get("__pyunostruct__")
    if type(name) is not str or len(name) > 240 or not _UNO_NAME.fullmatch(name):
        raise ProbeRefused("GENERATED_CLASS_IDENTITY")
    return name


def _exception_identity(error):
    cls = type(error)
    if type(cls) is not type:
        return "REDACTED_TYPE"
    d = _class_dict(cls)
    name = d.get("__pyunostruct__")
    if type(name) is str and len(name) <= 240 and _UNO_NAME.fullmatch(name):
        return name
    module = type.__getattribute__(cls, "__module__")
    name = type.__getattribute__(cls, "__name__")
    value = module + "." + name if type(module) is str and type(name) is str else ""
    return value if len(value) <= 240 and _BUILTIN_NAME.fullmatch(value) else "REDACTED_TYPE"


def exception_metadata(error):
    """Bounded class/edge/frame only; no args/Message/str/repr/locals/payload."""
    rows = []
    seen = set()
    node = error
    edge = "top"
    while isinstance(node, BaseException) and id(node) not in seen and len(rows) < 4:
        seen.add(id(node))
        frames = []
        tb = BaseException.__dict__["__traceback__"].__get__(node)
        while tb is not None and len(frames) < 8:
            code = tb.tb_frame.f_code
            source = code.co_filename.rsplit("/", 1)[-1]
            frames.append({"source": source if source in _SOURCE_NAMES else "OTHER_SOURCE",
                           "line": tb.tb_lineno})
            tb = tb.tb_next
        rows.append({"edge": edge, "exception_class": _exception_identity(node),
                     "source_frames": frames, "frames_truncated": tb is not None})
        cause = BaseException.__dict__["__cause__"].__get__(node)
        context = BaseException.__dict__["__context__"].__get__(node)
        node, edge = (cause, "cause") if cause is not None else (context, "context")
    return {"chain": rows, "chain_truncated_or_cycle": node is not None}


def generated_classes(*, include_setter=None):
    """Static type dictionaries, including uninstantiated bases AND structs.

    PyUNO caches newly generated base classes even if no instance invokes their
    setter. Scan object subclasses, rather than instances or frame locals.
    Builtin type.__subclasses__ bypasses user overrides. Bound before mutation.
    """
    todo = [(object, 0)]
    seen = set()
    found = []
    while todo:
        cls, depth = todo.pop()
        if id(cls) in seen:
            continue
        seen.add(id(cls))
        if len(seen) > 8192 or depth > 64:
            raise ProbeRefused("CLASS_SCAN_BOUND")
        children = type.__subclasses__(cls)
        todo.extend((child, depth + 1) for child in children)
        if type(cls) is type:
            d = _class_dict(cls)
            if "__pyunostruct__" in d:
                # Prescan admits exact generated identities. Postscan retains
                # malformed/changed identities so cleanup can restore our hook.
                if include_setter is None:
                    _uno_name(cls)
                found.append(cls)
            elif include_setter is not None and d.get("__setattr__") is include_setter:
                found.append(cls)
    return found


class OneShotConversionProbe:
    """One getRequest call total, with temporary, CAS-restored setter hooks.

    The accepted five-class compatibility token is checked, never replaced or
    broadened. Its class setters stay unchanged. The global helper only supplies
    instrumentation to newly generated classes. Unknown request remains unknown
    unless the probe actually observes a named class at the args setter seam.
    Even then its origin is RETURN_OR_ERROR_CONVERSION_UNKNOWN.
    """
    def __init__(self, uno, compat_token):
        self.uno = uno
        self.token = compat_token
        self.used = False

    def get_request(self, request, event):
        if self.used:
            raise ProbeRefused("ONE_GETREQUEST_ALREADY_CONSUMED")
        self.used = True
        if type(event) is not dict or event:
            raise ProbeRefused("EMPTY_METADATA_EVENT_REQUIRED")
        event.update(schema="friday.pyuno.conversion-metadata.v1", get_request_calls=0,
                     purpose="DIAGNOSTIC_NOT_ACCEPTANCE", setter_events=[],
                     setter_events_overflow=False, metadata_incomplete=False, restored=False,
                     origin="RETURN_OR_ERROR_CONVERSION_UNKNOWN")
        original = self.uno._uno_struct__setattr__
        if type(original) is not types.FunctionType:
            raise ProbeRefused("ORIGINAL_HELPER_FUNCTION_REQUIRED")
        if type(self.token) is not tuple or len(self.token) != len(_COMPAT_NAMES):
            raise ProbeRefused("EXACT_COMPAT_TOKEN_REQUIRED")
        accepted = {}
        for name, row in zip(_COMPAT_NAMES, self.token):
            if type(row) is not tuple or len(row) != 3:
                raise ProbeRefused("EXACT_COMPAT_ROW_REQUIRED")
            cls, old, replacement = row
            if (type(cls) is not type or not issubclass(cls, Exception)
                    or _uno_name(cls) != name or old is not original
                    or _class_dict(cls).get("__setattr__") is not replacement
                    or type(replacement) is not types.FunctionType or cls in accepted):
                raise ProbeRefused("EXACT_COMPAT_CAS_REQUIRED")
            accepted[cls] = replacement
        initial = generated_classes()
        initial_names = {cls: _uno_name(cls) for cls in initial}
        eligible = []
        for cls in initial:
            if not issubclass(cls, Exception):
                continue
            setter = _class_dict(cls).get("__setattr__")
            if cls in accepted:
                continue
            if setter is not original:
                raise ProbeRefused("FOREIGN_GENERATED_EXCEPTION_SETTER")
            eligible.append(cls)
        event["cached_exception_setters_planned"] = len(eligible)

        def observe_setter(value_self, name, value):
            # Never inspect value, value_self.value, or any payload field.
            row = None
            try:
                if type(name) is str and name == "args" and issubclass(type(value_self), Exception):
                    if len(event["setter_events"]) < 16:
                        row = {"generated_exception_class_during_conversion": _uno_name(type(value_self)),
                               "attribute": "args", "phase": "delegate_before"}
                        event["setter_events"].append(row)
                    else:
                        event["setter_events_overflow"] = True
            except BaseException:
                event["metadata_incomplete"] = True
            try:
                result = original(value_self, name, value)
            except BaseException as error:
                if row is not None:
                    row["phase"] = "delegate_exception_reraised"
                    try:
                        row["error"] = exception_metadata(error)
                    except BaseException:
                        event["metadata_incomplete"] = True
                raise
            else:
                if row is not None:
                    row["phase"] = "delegate_returned"
                return result

        changed = []
        helper_changed = False
        primary_failed = False
        try:
            # No UNO method is called during hook installation.
            self.uno._uno_struct__setattr__ = observe_setter
            helper_changed = True
            for cls in eligible:
                if _class_dict(cls).get("__setattr__") is not original:
                    raise ProbeRefused("PREINSTALL_CLASS_CAS")
                cls.__setattr__ = observe_setter
                changed.append(cls)
            event["get_request_calls"] = 1
            try:
                return request.getRequest()
            except BaseException as error:
                primary_failed = True
                try:
                    event["get_request_error"] = exception_metadata(error)
                except BaseException:
                    event["metadata_incomplete"] = True
                raise
        finally:
            # Postscan also catches newly cached, uninstantiated BASES/STRUCTS.
            cleanup_failures = []
            try:
                after = generated_classes(include_setter=observe_setter)
            except BaseException:
                after = list(changed)
                cleanup_failures.append("POSTSCAN_FAILED")
            restored = 0
            for cls in set(after).union(initial):
                try:
                    final_name = _uno_name(cls)
                    if cls in initial_names and final_name != initial_names[cls]:
                        cleanup_failures.append("GENERATED_CLASS_IDENTITY_DRIFT")
                except BaseException:
                    cleanup_failures.append("GENERATED_CLASS_IDENTITY_DRIFT")
                current = _class_dict(cls).get("__setattr__")
                if current is observe_setter:
                    try:
                        cls.__setattr__ = original
                        restored += 1
                    except BaseException:
                        cleanup_failures.append("SETTER_RESTORE_FAILED")
                elif cls in changed or cls not in initial_names:
                    cleanup_failures.append("SETTER_RESTORE_CAS_DRIFT")
            if helper_changed:
                try:
                    helper_current = self.uno._uno_struct__setattr__
                except BaseException:
                    cleanup_failures.append("HELPER_RESTORE_CAS_DRIFT")
                else:
                    if helper_current is observe_setter:
                        try:
                            self.uno._uno_struct__setattr__ = original
                        except BaseException:
                            cleanup_failures.append("HELPER_RESTORE_FAILED")
                    else:
                        cleanup_failures.append("HELPER_RESTORE_CAS_DRIFT")
            for cls, expected in accepted.items():
                if _class_dict(cls).get("__setattr__") is not expected:
                    cleanup_failures.append("COMPAT_SETTER_DRIFT")
            event["setters_restored"] = restored
            event["cleanup_failures"] = cleanup_failures
            event["restored"] = not cleanup_failures
            if cleanup_failures and not primary_failed:
                raise ProbeRefused("HOOK_RESTORE_FAILED_PRIVATE_CLIENT_MUST_EXIT")
