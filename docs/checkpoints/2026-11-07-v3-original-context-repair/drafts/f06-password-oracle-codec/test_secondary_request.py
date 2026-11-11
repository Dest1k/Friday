"""Delta controls only; immutable original 65+66 controls remain reused."""
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import callback_observer_v2 as observer
import request_args_compat_v2 as compat

ROOT = Path(__file__).resolve().parent
checks = []


def check(name, value):
    checks.append({"name": name, "pass": bool(value)})
    if not value:
        raise AssertionError(name)


def raises(kind, operation):
    try:
        operation()
    except kind:
        return True
    return False


def original(self, name, value):
    if name not in ("ErrCode", "Arg1", "Arg2", "Message", "Name"):
        raise AttributeError(name)
    self.__dict__["material"][name] = value


def init(self):
    self.__dict__["material"] = {}


def getter(self, name):
    return self.__dict__["material"][name]


classes = {}
for name in compat.REQUEST_NAMES:
    parent = classes.get(name[:-1], Exception) if name.endswith("2") else Exception
    classes[name] = type(name, (parent,), {"__setattr__": original, "__getattr__": getter, "__pyunostruct__": name, "__init__": init})
uno = SimpleNamespace(_uno_struct__setattr__=original, getClass=classes.__getitem__, getTypeByName=lambda name: name)
error_cls = classes["com.sun.star.task.ErrorCodeRequest2"]
check("fifth_exact_class_only", compat.REQUEST_NAMES[-1] == "com.sun.star.task.ErrorCodeRequest2" and len(compat.REQUEST_NAMES) == 5)
check("error_payload_original_args_refuses", raises(AttributeError, lambda: setattr(error_cls(), "args", ("",))))
classes[compat.REQUEST_NAMES[-1]].__setattr__ = BaseException.__setattr__
check("fifth_preflight_rejects_changed_setter", raises(ValueError, lambda: compat.install_request_args_compat(uno)))
check("fifth_preflight_no_partial_first_four_patch", all(classes[n].__dict__["__setattr__"] is original for n in compat.REQUEST_NAMES[:4]))
classes[compat.REQUEST_NAMES[-1]].__setattr__ = original
token = compat.install_request_args_compat(uno)
check("exact_five_validated_and_patched", len(token) == 5)
e = error_cls()
e.args = ("",)
e.ErrCode = 283
check("fifth_args_uses_baseexception", e.args == ("",) and e.__dict__["material"] == {"ErrCode": 283})
check("fifth_errcode_delegates_original", e.ErrCode == 283)
check("global_setter_unchanged", uno._uno_struct__setattr__ is original)
check("repeat_install_still_refuses", raises(ValueError, lambda: compat.install_request_args_compat(uno)))


class Base:
    pass


class Interface:
    pass


class Continuation:
    selected = False
    def queryInterface(self, wanted):
        return self
    def select(self):
        self.selected = True


class Request:
    def __init__(self, payload_cls, code=283):
        self.payload_cls = payload_cls
        self.code = code
        self.continuation = Continuation()
    def getRequest(self):
        payload = self.payload_cls()
        payload.args = ("",)
        if self.payload_cls is error_cls:
            payload.ErrCode = self.code
        return payload
    def getContinuations(self):
        return (self.continuation,)


def handler(with_error_type=True):
    return observer.make_abort_handler(uno, SimpleNamespace(Base=Base), Interface, classes[compat.REQUEST_NAMES[0]], classes[compat.REQUEST_NAMES[1]], error_cls if with_error_type else None)


h = handler()
h.handle(Request(classes[compat.REQUEST_NAMES[2]]))
h.handle(Request(error_cls))
events = h.events
check("secondary_typed_request_and_code_observed", events[1]["request_kind"] == "ErrorCodeRequest2" and events[1]["payload_class"] == "com.sun.star.task.ErrorCodeRequest2" and events[1]["error_code"] == 283)
check("secondary_selected_after_code_observation", events[1]["phases"].index("error_code_after") < events[1]["phases"].index("select_before") and events[1]["phase"] == "select_after")
for fmt in ("odt", "ods", "odp"):
    check(fmt + "_exact_sequence_supported", observer.observed_password_refusal_sequence(events, fmt))
for fmt in ("docx", "xlsx", "pptx", "rtf", "", None):
    check(str(fmt) + "_standard_secondary_sequence_refused", not observer.observed_password_refusal_sequence(events, fmt))
check("old_all_password_predicate_stays_false_on_secondary", not observer.observed_password_abort(events))
check("secondary_alone_rejected", not observer.observed_password_refusal_sequence(events[1:], "odt"))
check("password_alone_rejected_for_known_odf_path", not observer.observed_password_refusal_sequence(events[:1], "odt"))
check("swapped_order_rejected", not observer.observed_password_refusal_sequence(list(reversed(events)), "odt"))
check("extra_callback_rejected", not observer.observed_password_refusal_sequence(events + [events[1]], "odt"))
check("empty_events_rejected", not observer.observed_password_refusal_sequence([], "odt"))
check("none_events_rejected", not observer.observed_password_refusal_sequence(None, "odt"))
for code in (0, 1, 27, 282, 284, 308, 0x1011B, -1, True, "283", None):
    changed = [dict(events[0]), dict(events[1], error_code=code)]
    check("other_or_malformed_code_" + str(code) + "_rejected", not observer.observed_password_refusal_sequence(changed, "odt"))
for field, value in (("payload_class", "com.sun.star.task.ErrorCodeRequest"), ("request_kind", "OTHER"), ("is_error_code_request2", False), ("abort_selected", False), ("phase", "select_before"), ("callback_error", {}), ("callback_error_phase", "get_request_before")):
    changed = [dict(events[0]), dict(events[1], **{field: value})]
    check("bad_secondary_" + field + "_rejected", not observer.observed_password_refusal_sequence(changed, "odt"))
for field, value in (("request_kind", "OTHER"), ("request_kind", "DocumentMSPasswordRequest"), ("abort_selected", False), ("phase", "select_before"), ("callback_error", {})):
    changed = [dict(events[0], **{field: value}), dict(events[1])]
    check("bad_primary_" + field + "_rejected", not observer.observed_password_refusal_sequence(changed, "odt"))
h = handler()
h.handle(Request(classes[compat.REQUEST_NAMES[3]]))
for fmt in ("docx", "xlsx", "pptx"):
    check(fmt + "_single_ms_abort_unchanged", observer.observed_password_refusal_sequence(h.events, fmt))
check("ms_with_secondary_rejected", not observer.observed_password_refusal_sequence(h.events + [events[1]], "docx"))

for code in (True, "283", None, 2**31, -(2**31)-1):
    h = handler()
    check("invalid_native_errcode_type_or_range_" + str(code), raises(ValueError, lambda: h.handle(Request(error_cls, code))))
    check("invalid_errcode_not_selected_" + str(code), h.events[0]["callback_error_phase"] == "error_code_before" and h.events[0]["abort_selected"] is False)
h = handler(False)
h.handle(Request(error_cls))
check("missing_injected_exact_error_type_not_classified", h.events[0]["request_kind"] == "OTHER" and "error_code" not in h.events[0])
compat.restore_request_args_compat(token)
check("all_five_originals_restored", all(cls.__dict__["__setattr__"] is original for cls in classes.values()))

tree = ast.parse((ROOT / "callback_observer_v2.py").read_text())
attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
check("only_approved_typed_error_field_read", "ErrCode" in attrs and not attrs.intersection({"Arg1", "Arg2", "DialogMask", "Message", "ErrorCode", "ArgumentPosition", "Password", "Name", "args", "f_locals", "f_globals"}))
check("no_new_process_network_or_file_imports", [n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)] == ["re"])
check("five_scope_no_ioexception_or_base_errorcode", "com.sun.star.task.ErrorCodeIOException" not in compat.REQUEST_NAMES and "com.sun.star.task.ErrorCodeRequest" not in compat.REQUEST_NAMES)
report = {"schema": "friday.f06.secondary-error-request.delta-pure-controls.v1", "all_pass": all(c["pass"] for c in checks), "count": len(checks), "checks": checks, "observer_v2_sha256": hashlib.sha256((ROOT / "callback_observer_v2.py").read_bytes()).hexdigest(), "compat_v2_sha256": hashlib.sha256((ROOT / "request_args_compat_v2.py").read_bytes()).hexdigest(), "execution": "pure Python fake classes only; no Office/PyUNO imports", "native_secondary_type_not_observed_here": True}
(ROOT / "SECONDARY-PURE-CONTROLS.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"all_pass": report["all_pass"], "count": report["count"]}))
