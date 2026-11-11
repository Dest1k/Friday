"""Meaningful pure negative controls. Fakes exercise no UNO/Office or filesystem input."""
import copy
import hashlib
import json
from pathlib import Path
import latest_odt_interaction_probe as p

checks = []


def check(name, condition):
    if condition is not True:
        raise AssertionError(name)
    checks.append(name)


class Payload:
    def __init__(self, mode="enter", modify=False, name=p.LATEST_URL):
        self.Mode = mode
        self.IsRequestPasswordToModify = modify
        self.Name = name


DocumentPasswordRequest2 = type("DocumentPasswordRequest2", (Payload,), {"__module__": "com.sun.star.task"})
ErrorCodeRequest2 = type("ErrorCodeRequest2", (), {"__module__": "com.sun.star.task"})


def error_payload(code):
    payload = ErrorCodeRequest2()
    payload.ErrCode = code
    return payload


class PoisonError(Exception):
    def __str__(self):
        raise AssertionError("exception_str_was_used")

    def __repr__(self):
        raise AssertionError("exception_repr_was_used")


class Abort:
    def __init__(self, fail=False):
        self.selected = False
        self.fail = fail

    def queryInterface(self, requested):
        return self if requested == "com.sun.star.task.XInteractionAbort" else None

    def select(self):
        if self.fail:
            raise PoisonError("PRIVATE_PURE_SENTINEL")
        self.selected = True


class Password:
    def __init__(self, expected, fail_set=False, fail_select=False):
        self.expected = expected
        self.supplied_correctly = False
        self.set_count = 0
        self.select_count = 0
        self.fail_set = fail_set
        self.fail_select = fail_select

    def queryInterface(self, requested):
        return self if requested == "com.sun.star.task.XInteractionPassword2" else None

    def setPassword(self, value):
        self.set_count += 1
        self.supplied_correctly = type(value) is str and value == self.expected and bool(value)
        if self.fail_set:
            raise PoisonError("PRIVATE_PURE_SENTINEL")

    def select(self):
        self.select_count += 1
        if self.fail_select:
            raise PoisonError("PRIVATE_PURE_SENTINEL")


class Request:
    def __init__(self, payload, continuations):
        self.payload = payload
        self.continuations = continuations

    def getRequest(self):
        return self.payload

    def getContinuations(self):
        return self.continuations


class Uno:
    @staticmethod
    def getTypeByName(name):
        return name


class UnoHelper:
    class Base:
        pass


class XInteractionHandler:
    pass


def handler(case="wrong", password="PRIVATE_PURE_WRONG"):
    return p.make_handler(Uno, UnoHelper, XInteractionHandler, DocumentPasswordRequest2,
                          ErrorCodeRequest2, "enter", "reenter", case, password)


def callback(h, payload, expected="PRIVATE_PURE_WRONG", **kwargs):
    abort = Abort(kwargs.pop("fail_abort", False))
    secret = Password(expected, **kwargs)
    h.handle(Request(payload, (abort, secret)))
    return abort, secret


class Doc:
    def __init__(self, fail_close=False, fail_dispose=False):
        self.closed = False
        self.disposed = False
        self.fail_close = fail_close
        self.fail_dispose = fail_dispose

    def close(self, ownership):
        check("close_boolean_ownership", ownership is True)
        if self.fail_close:
            raise PoisonError("PRIVATE_PURE_SENTINEL")
        self.closed = True

    def dispose(self):
        if self.fail_dispose:
            raise PoisonError("PRIVATE_PURE_SENTINEL")
        self.disposed = True


class Desktop:
    def __init__(self, wrong_generic=False, fail_close=False, fail_load=False, wrong_open_cleanup_fault=False):
        self.loads = []
        self.wrong_generic = wrong_generic
        self.fail_close = fail_close
        self.fail_load = fail_load
        self.wrong_open_cleanup_fault = wrong_open_cleanup_fault
        self.docs = []

    def loadComponentFromURL(self, url, frame, flags, properties):
        self.loads.append((url, frame, flags))
        check("fixed_target_" + str(len(self.loads)), url == p.LATEST_URL)
        check("blank_frame_" + str(len(self.loads)), frame == "_blank" and flags == 0)
        names = tuple(name for name, value in properties)
        check("no_media_credentials_" + str(len(self.loads)), names == (
            "Hidden", "ReadOnly", "MacroExecutionMode", "UpdateDocMode", "InteractionHandler"))
        prop = dict(properties)
        check("readonly_hidden_" + str(len(self.loads)), prop["Hidden"] is True and prop["ReadOnly"] is True)
        check("macros_updates_disabled_" + str(len(self.loads)),
              type(prop["MacroExecutionMode"]) is int and prop["MacroExecutionMode"] == 0
              and type(prop["UpdateDocMode"]) is int and prop["UpdateDocMode"] == 0)
        h = prop["InteractionHandler"]
        case = ("missing", "wrong", "correct")[len(self.loads) - 1]
        if case == "wrong" and self.wrong_generic:
            callback(h, error_payload(525))
            return None
        expected = "PRIVATE_PURE_CORRECT" if case == "correct" else "PRIVATE_PURE_WRONG"
        callback(h, DocumentPasswordRequest2(), expected)
        if case != "correct":
            if case == "wrong" and self.wrong_open_cleanup_fault:
                doc = Doc(fail_close=True, fail_dispose=True)
                self.docs.append(doc)
                return doc
            if case == "wrong":
                callback(h, DocumentPasswordRequest2("reenter"), expected)
            callback(h, error_payload(283))
            return None
        if self.fail_load:
            raise PoisonError("PRIVATE_PURE_SENTINEL")
        doc = Doc(self.fail_close)
        self.docs.append(doc)
        return doc


def run(desktop=None, custody=None, semantic=None, **kwargs):
    return p.run_latest_three(desktop=desktop or Desktop(), uno=Uno, unohelper=UnoHelper,
        XInteractionHandler=XInteractionHandler, DocumentPasswordRequest2=DocumentPasswordRequest2,
        ErrorCodeRequest2=ErrorCodeRequest2, enter_mode="enter", reenter_mode="reenter",
        property_factory=lambda n, v: (n, v), wrong_password="PRIVATE_PURE_WRONG",
        correct_password="PRIVATE_PURE_CORRECT", semantic_checker=semantic or (lambda doc: True),
        assert_current_custody=custody or (lambda: True), **kwargs)


def main():
    h = handler()
    a, s = callback(h, DocumentPasswordRequest2())
    check("first_enter_supplied_selected_once", s.supplied_correctly and s.set_count == 1 and s.select_count == 1 and not a.selected)
    check("secret_reference_cleared_after_supply", h._password is None)
    a, s = callback(h, DocumentPasswordRequest2("reenter"))
    check("reenter_aborted_without_second_supply", a.selected and s.set_count == 0 and s.select_count == 0)
    callback(h, error_payload(283))
    check("exact_wrong_sequence_accepted", p.observed_sequence(h.events, "wrong"))
    valid_wrong = copy.deepcopy(h.events)
    mutations = (
        ("wrong_generic_525_rejected", lambda e: [e[2] | {"error_code": 525}]),
        ("wrong_no_reenter_rejected", lambda e: [e[0], e[2]]),
        ("wrong_reordered_rejected", lambda e: [e[1], e[0], e[2]]),
        ("wrong_extra_event_rejected", lambda e: e + [e[2]]),
        ("wrong_blank_supply_not_evidence", lambda e: [e[0] | {"password_supplied": False}, *e[1:]]),
        ("wrong_without_select_not_evidence", lambda e: [e[0] | {"password_selected": False}, *e[1:]]),
        ("wrong_second_enter_not_evidence", lambda e: [e[0], e[1] | {"mode": "PASSWORD_ENTER"}, e[2]]),
        ("wrong_modify_request_not_evidence", lambda e: [e[0] | {"password_to_modify": True}, *e[1:]]),
        ("wrong_offtarget_request_not_evidence", lambda e: [e[0] | {"target_matches": False}, *e[1:]]),
        ("wrong_untyped_payload_not_evidence", lambda e: [e[0] | {"payload_class": "OTHER"}, *e[1:]]),
        ("wrong_callback_error_not_evidence", lambda e: [e[0] | {"callback_error_class": "builtins.ValueError"}, *e[1:]]),
        ("wrong_unfinished_select_not_evidence", lambda e: [e[0], e[1] | {"phase": "select_abort_before"}, e[2]]),
        ("wrong_error_bool_not_evidence", lambda e: [*e[:2], e[2] | {"error_code": True}]),
        ("wrong_error_string_not_evidence", lambda e: [*e[:2], e[2] | {"error_code": "283"}]),
        ("wrong_error_525_after_reenter_not_evidence", lambda e: [*e[:2], e[2] | {"error_code": 525}]),
    )
    for name, mutate in mutations:
        check(name, not p.observed_sequence(mutate(copy.deepcopy(valid_wrong)), "wrong"))
    check("overflow_not_evidence", not p.observed_sequence(valid_wrong, "wrong", True))
    check("non_list_events_rejected", not p.observed_sequence(tuple(valid_wrong), "wrong"))
    check("unknown_case_rejected", not p.observed_sequence(valid_wrong, "OTHER"))
    for label, payload in (("initial_reenter", DocumentPasswordRequest2("reenter")),
                           ("create_or_unknown_mode", DocumentPasswordRequest2("create")),
                           ("modify", DocumentPasswordRequest2(modify=True)),
                           ("offtarget_name", DocumentPasswordRequest2(name="file:///inputs/other.odt")),
                           ("untyped_name", DocumentPasswordRequest2(name=object())),
                           ("foreign_payload", object()),
                           ("subclass_payload", type("Derived", (DocumentPasswordRequest2,), {})())):
        negative = handler()
        a, s = callback(negative, payload)
        check(label + "_never_supplied", a.selected and s.set_count == 0)
    missing = handler("missing", None)
    a, s = callback(missing, DocumentPasswordRequest2())
    check("missing_aborts_without_secret", a.selected and s.set_count == 0)
    callback(missing, error_payload(283))
    check("missing_exact_sequence", p.observed_sequence(missing.events, "missing"))
    for label, kwargs in (("set_fault", {"fail_set": True}), ("select_fault", {"fail_select": True})):
        fault = handler()
        try:
            callback(fault, DocumentPasswordRequest2(), **kwargs)
        except RuntimeError as error:
            check(label + "_bridge_exception_sanitized", str(error) == "latest_odt_callback_failure"
                  and error.__cause__ is None and error.__suppress_context__ is True)
        else:
            raise AssertionError("callback_fault_was_swallowed")
        check(label + "_logged_type_only", fault.events[0]["callback_error_class"].endswith("PoisonError")
              and "PRIVATE_PURE" not in json.dumps(fault.events))
        check(label + "_secret_cleared", fault._password is None)
        a, s = callback(fault, DocumentPasswordRequest2())
        check(label + "_never_resubmits", a.selected and s.set_count == 0)
    for value in (None, "", 0, False):
        try:
            handler("wrong", value)
        except ValueError:
            check("empty_or_untyped_password_rejected_" + str(type(value).__name__), True)
        else:
            raise AssertionError("empty_password_was_accepted")
    counter = []
    desktop = Desktop()
    result = run(desktop, lambda: counter.append(True) is None)
    check("three_case_positive_control", result["diagnostic_interaction_all_pass"] is True)
    check("exactly_three_latest_loads", len(desktop.loads) == 3 and result["loads"] == 3)
    check("custody_before_after_each_load", len(counter) == 6)
    check("doc_closed", len(desktop.docs) == 1 and desktop.docs[0].closed)
    check("no_secrets_serialized", "PRIVATE_PURE" not in json.dumps(result))
    generic = run(Desktop(wrong_generic=True))
    check("generic_525_does_not_promote", generic["diagnostic_interaction_all_pass"] is False
          and generic["tests"]["wrong"]["diagnostic_case_pass"] is False)
    check("semantic_control_required", run(semantic=lambda doc: False)["diagnostic_interaction_all_pass"] is False)
    close_fault = Desktop(fail_close=True)
    closed = run(close_fault)
    check("close_failure_not_pass", closed["diagnostic_interaction_all_pass"] is False and close_fault.docs[0].disposed)
    cleanup_fault = Desktop(wrong_open_cleanup_fault=True)
    stopped = run(cleanup_fault)
    check("unconfirmed_cleanup_stops_remaining_loads", len(cleanup_fault.loads) == 2 and stopped["loads"] == 2)
    check("unconfirmed_cleanup_never_all_pass", stopped["diagnostic_interaction_all_pass"] is False
          and stopped["halt_reason"] == "document_cleanup_unconfirmed_Root_must_close_own_Office_unit"
          and "correct" not in stopped["tests"])
    load_fault = run(Desktop(fail_load=True))
    check("load_exception_not_evidence", load_fault["diagnostic_interaction_all_pass"] is False)
    check("load_exception_type_only", "PRIVATE_PURE" not in json.dumps(load_fault))
    for label, target in (("other_six", "file:///inputs/encrypted-inputs/other.docx"),
                          ("alternate_alias", "file:///inputs/encrypted-inputs/./f06-new-default-latest.odt")):
        desktop = Desktop()
        try:
            run(desktop, target_url=target)
        except ValueError:
            check(label + "_rejected_before_load", len(desktop.loads) == 0)
        else:
            raise AssertionError("target_was_not_rejected")
    desktop = Desktop()
    try:
        run(desktop, custody=lambda: False)
    except ValueError:
        check("custody_failure_prevents_first_load", len(desktop.loads) == 0)
    else:
        raise AssertionError("custody_was_not_required")
    desktop = Desktop()
    custody_calls = []
    try:
        run(desktop, custody=lambda: custody_calls.append(True) is None and len(custody_calls) < 2)
    except ValueError:
        check("after_custody_failure_stops_remaining_loads", len(desktop.loads) == 1)
    else:
        raise AssertionError("after_custody_was_not_required")
    path = Path(__file__).with_name("PURE-CONTROLS.json")
    output = {"status": "PASS", "pure_check_count": len(checks), "checks": checks,
              "candidate_sha256": hashlib.sha256(Path(p.__file__).read_bytes()).hexdigest(),
              "Office": "NOT_RUN", "UNO": "NOT_IMPORTED", "actual_input_reads": 0}
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "PASS", "pure_check_count": len(checks)}))


if __name__ == "__main__":
    main()
