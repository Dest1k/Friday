"""DORMANT Root-only latest ODT diagnostic. No imports of UNO, no launcher.

Root injects admitted UNO objects inside its existing readonly sandbox, fresh
client, pinned exact-five request-args compatibility, deadline and cleanup.
This module writes no files and changes no registry or earlier result. Its only
load target is the retained latest ODT. All three loads OMIT Password and
EncryptionData. No secret, request payload, exception value or document content
is returned. Correct semantics are checked in memory by Root's existing checker.

PASSWORD_REENTER proves the Office verifier rejected a nonempty submitted
password. This verifier ALSO maps arbitrary UNO exceptions to WrongPassword;
same-byte successful correct semantics and custody are essential controls.
Neither IO525 nor any generic load failure is password rejection evidence.
"""

import re

LATEST_URL = "file:///inputs/encrypted-inputs/f06-new-default-latest.odt"
LATEST_SHA256 = "29504a7e57afbd0c6451e16d774117c820d0e2fa9ba1f92651437f676fe3672e"
IO_ABORT = 283
_QUALIFIED = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){0,16}\Z")


def safe_type(value):
    cls = type(value)
    name = cls.__name__
    module = cls.__module__
    candidate = name if "." in name else module + "." + name
    return candidate if len(candidate) <= 240 and _QUALIFIED.fullmatch(candidate) else "REDACTED_TYPE"


def make_handler(uno, unohelper, XInteractionHandler, DocumentPasswordRequest2,
                 ErrorCodeRequest2, enter_mode, reenter_mode, case, password=None):
    """Supply at most once, only to exact standard opening ENTER; otherwise Abort.

    Type/enum bindings come from the already admitted process. Request2 is exact
    because the pinned Standard source always constructs DocumentPasswordRequest2.
    XInteractionPassword2 inherits XInteractionPassword and is what that source
    exposes. A later callback can never receive another secret submission.
    """
    if case not in ("missing", "wrong", "correct"):
        raise ValueError("diagnostic_case_contract")
    if case == "missing":
        if password is not None:
            raise ValueError("missing_has_no_password")
    elif type(password) is not str or not password:
        raise ValueError("nonempty_password_required")
    if enter_mode == reenter_mode:
        raise ValueError("distinct_modes_required")
    abort_type = uno.getTypeByName("com.sun.star.task.XInteractionAbort")
    password_type = uno.getTypeByName("com.sun.star.task.XInteractionPassword2")

    class Handler(unohelper.Base, XInteractionHandler):
        def __init__(self):
            self.events = []
            self.overflow = False
            self._password = password
            self._submission_attempted = False

        def handle(self, request):
            event = {"phase": "entered", "request_kind": "UNCLASSIFIED",
                     "password_supplied": False, "password_selected": False,
                     "abort_selected": False}
            # Expected maximum is three events. Extra callbacks reject even if
            # aborted; Root's external deadline still owns process termination.
            if len(self.events) < 4:
                self.events.append(event)
            else:
                self.overflow = True
            try:
                event["phase"] = "get_request_before"
                payload = request.getRequest()
                event["payload_class"] = safe_type(payload)
                event["phase"] = "classify_before"
                if type(payload) is DocumentPasswordRequest2:
                    event["request_kind"] = "DocumentPasswordRequest2"
                    mode = payload.Mode
                    event["mode"] = ("PASSWORD_ENTER" if mode == enter_mode else
                                     "PASSWORD_REENTER" if mode == reenter_mode else "OTHER")
                    modify = payload.IsRequestPasswordToModify
                    if type(modify) is not bool:
                        raise TypeError("typed_modify_flag_required")
                    event["password_to_modify"] = modify
                    # Name is a document URL, never log its value. Correlate
                    # before handing a secret to any offered continuation.
                    name = payload.Name
                    event["target_matches"] = type(name) is str and name == LATEST_URL
                elif type(payload) is ErrorCodeRequest2:
                    event["request_kind"] = "ErrorCodeRequest2"
                    code = payload.ErrCode
                    if type(code) is not int or not -(2**31) <= code < 2**31:
                        raise TypeError("typed_error_code_required")
                    event["error_code"] = code
                else:
                    event["request_kind"] = "OTHER"
                event["phase"] = "get_continuations_before"
                continuations = request.getContinuations()
                supply = (not self.overflow and len(self.events) == 1
                          and case != "missing" and not self._submission_attempted
                          and event["request_kind"] == "DocumentPasswordRequest2"
                          and event["mode"] == "PASSWORD_ENTER"
                          and event["password_to_modify"] is False
                          and event["target_matches"] is True)
                if supply:
                    for continuation in continuations:
                        event["phase"] = "query_password_before"
                        password_continuation = continuation.queryInterface(password_type)
                        if password_continuation is not None:
                            # Commit once before entering either UNO method.
                            self._submission_attempted = True
                            event["phase"] = "set_password_before"
                            try:
                                password_continuation.setPassword(self._password)
                                event["password_supplied"] = True
                            finally:
                                self._password = None
                            event["phase"] = "select_password_before"
                            password_continuation.select()
                            event["password_selected"] = True
                            event["phase"] = "password_select_after"
                            return
                    raise RuntimeError("password_continuation_unavailable")
                self._password = None
                for continuation in continuations:
                    event["phase"] = "query_abort_before"
                    abort = continuation.queryInterface(abort_type)
                    if abort is not None:
                        event["phase"] = "select_abort_before"
                        abort.select()
                        event["abort_selected"] = True
                        event["phase"] = "abort_select_after"
                        return
                raise RuntimeError("abort_continuation_unavailable")
            except Exception as error:
                self._password = None
                event["callback_error_phase"] = event["phase"]
                event["callback_error_class"] = safe_type(error)
                event["phase"] = "callback_fault_sanitized"
                # PyUNO stringifies callback exceptions (pyuno_runtime.cxx:
                # 929–949). Never let an original UNO/Python message cross the
                # bridge. Its traceback prints source lines, without locals.
                raise RuntimeError("latest_odt_callback_failure") from None

    return Handler()


def _password_event(event, mode, supplied):
    return (type(event) is dict
            and event.get("request_kind") == "DocumentPasswordRequest2"
            and event.get("payload_class") == "com.sun.star.task.DocumentPasswordRequest2"
            and event.get("mode") == mode and event.get("password_to_modify") is False
            and event.get("target_matches") is True
            and event.get("password_supplied") is supplied
            and event.get("password_selected") is supplied
            and event.get("abort_selected") is (not supplied)
            and event.get("phase") == ("password_select_after" if supplied else "abort_select_after")
            and "callback_error_class" not in event and "callback_error_phase" not in event)


def _abort_event(event):
    return (type(event) is dict and event.get("request_kind") == "ErrorCodeRequest2"
            and event.get("payload_class") == "com.sun.star.task.ErrorCodeRequest2"
            and type(event.get("error_code")) is int and event["error_code"] == IO_ABORT
            and event.get("password_supplied") is False and event.get("password_selected") is False
            and event.get("abort_selected") is True and event.get("phase") == "abort_select_after"
            and "callback_error_class" not in event and "callback_error_phase" not in event)


def observed_sequence(events, case, overflow=False):
    """Necessary event evidence only. Never use without unopened/positive/CAS checks."""
    if type(events) is not list or overflow is not False:
        return False
    if case == "missing":
        return (len(events) == 2 and _password_event(events[0], "PASSWORD_ENTER", False)
                and _abort_event(events[1]))
    if case == "wrong":
        return (len(events) == 3 and _password_event(events[0], "PASSWORD_ENTER", True)
                and _password_event(events[1], "PASSWORD_REENTER", False) and _abort_event(events[2]))
    if case == "correct":
        return len(events) == 1 and _password_event(events[0], "PASSWORD_ENTER", True)
    return False


def run_latest_three(*, desktop, uno, unohelper, XInteractionHandler,
                     DocumentPasswordRequest2, ErrorCodeRequest2, enter_mode, reenter_mode,
                     property_factory, wrong_password, correct_password,
                     semantic_checker, assert_current_custody, target_url=LATEST_URL):
    """ONLY Root may invoke after separate exact-source admission. No CLI/launcher.

    assert_current_custody must verify the admitted original+staged identity,
    readonly/path/link/owner/hash/current CAS before/after each load. It returns
    exactly True, otherwise no further probe runs. No custody implementation is
    bypassed or replaced here. Root must preserve each raw result independently.
    """
    if target_url != LATEST_URL:
        raise ValueError("latest_only_fixed_namespace_target")
    if (type(wrong_password) is not str or type(correct_password) is not str
            or not wrong_password or not correct_password or wrong_password == correct_password):
        raise ValueError("distinct_nonempty_credentials_required")
    results = {}
    halt_reason = None
    for case, password in (("missing", None), ("wrong", wrong_password), ("correct", correct_password)):
        if assert_current_custody() is not True:
            raise ValueError("current_custody_required_before")
        handler = make_handler(uno, unohelper, XInteractionHandler, DocumentPasswordRequest2,
                               ErrorCodeRequest2, enter_mode, reenter_mode, case, password)
        # Deliberately no Password or EncryptionData property on ANY load.
        properties = tuple(property_factory(name, value) for name, value in (
            ("Hidden", True), ("ReadOnly", True), ("MacroExecutionMode", 0),
            ("UpdateDocMode", 0), ("InteractionHandler", handler)))
        doc = None
        answer = {"opened": False, "semantic_match": False, "closed": False}
        try:
            doc = desktop.loadComponentFromURL(target_url, "_blank", 0, properties)
            if doc is not None:
                answer["opened"] = True
                if case == "correct":
                    try:
                        answer["semantic_match"] = semantic_checker(doc) is True
                    except Exception as error:
                        answer["semantic_exception_class"] = safe_type(error)
        except Exception as error:
            answer["load_exception_class"] = safe_type(error)
        finally:
            answer["component_reference_cleanup_confirmed"] = doc is None
            if doc is not None:
                try:
                    doc.close(True)
                    answer["closed"] = True
                    answer["component_reference_cleanup_confirmed"] = True
                except Exception as error:
                    answer["close_exception_class"] = safe_type(error)
                    try:
                        doc.dispose()
                        answer["disposed_after_close_error"] = True
                        answer["component_reference_cleanup_confirmed"] = True
                    except Exception as dispose_error:
                        answer["dispose_exception_class"] = safe_type(dispose_error)
            answer["interaction_events"] = handler.events
            answer["callback_overflow"] = handler.overflow
            if assert_current_custody() is not True:
                raise ValueError("current_custody_required_after")
        sequence = observed_sequence(handler.events, case, handler.overflow)
        answer["observed_expected_sequence"] = sequence
        no_fault = not any(key.endswith("exception_class") for key in answer)
        answer["diagnostic_case_pass"] = bool(sequence and no_fault and (
            (case == "correct" and answer["opened"] and answer["semantic_match"] and answer["closed"])
            or (case != "correct" and not answer["opened"] and doc is None)))
        results[case] = answer
        if answer["component_reference_cleanup_confirmed"] is not True:
            halt_reason = "document_cleanup_unconfirmed_Root_must_close_own_Office_unit"
            break
    return {"scope": "latest_odt_only_interaction_path", "source_sha256": LATEST_SHA256,
            "stores": 0, "loads": len(results), "credential_submission_limit_per_load": 1,
            "halt_reason": halt_reason,
            "tests": results, "diagnostic_interaction_all_pass": len(results) == 3 and all(
                row["diagnostic_case_pass"] for row in results.values()),
            "proof_limit": "Office_verifier_rejection_with_same_byte_positive_control_not_cryptographic_cause"}
