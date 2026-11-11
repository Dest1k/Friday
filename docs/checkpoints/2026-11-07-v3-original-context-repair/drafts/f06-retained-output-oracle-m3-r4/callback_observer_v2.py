"""DORMANT source-only F06 callback instrumentation; imports no UNO and runs no Office.

Root injects already admitted UNO objects. Preserve original handler decisions and
re-raise callback faults. This observer NEVER promotes a load failure to a password
refusal. Do not serialize payload/request/continuation objects or exception values.
"""
import re

_QUALIFIED = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){0,16}\Z")
_FRAME_FILES = frozenset(("callback_observer.py", "callback_observer_v2.py", "office_fixture_driver.py", "uno.py", "unohelper.py"))


def safe_type(value):
    """Class identity only; UNO generated __name__ can already be qualified."""
    cls = type(value)
    name = cls.__name__
    module = cls.__module__
    candidate = name if "." in name else module + "." + name
    return candidate if len(candidate) <= 240 and _QUALIFIED.fullmatch(candidate) else "REDACTED_TYPE"


def safe_exception(error):
    """No Message, str/repr, args, locals, payload fields or file paths."""
    frames = []
    tb = error.__traceback__
    while tb is not None and len(frames) < 12:
        code = tb.tb_frame.f_code
        filename = code.co_filename.rsplit("/", 1)[-1]
        filename = filename if filename in _FRAME_FILES else "OTHER_SOURCE"
        function = code.co_name
        if len(function) > 100 or not _QUALIFIED.fullmatch(function):
            function = "OTHER_FUNCTION"
        frames.append({"source": filename, "function": function, "line": tb.tb_lineno})
        tb = tb.tb_next
    return {"exception_class": safe_type(error), "source_frames": frames}


def make_abort_handler(uno, unohelper, XInteractionHandler, DocumentPasswordRequest, DocumentMSPasswordRequest, ErrorCodeRequest2=None):
    """Only the existing callback is instrumented; selection semantics unchanged."""
    class AbortInteractions(unohelper.Base, XInteractionHandler):
        def __init__(self):
            self.events = []

        def handle(self, request):
            # FIRST callback operation: make an event before any UNO/type operation.
            event = {"phase": "entered", "phases": ["entered"], "request_kind": "UNCLASSIFIED", "abort_selected": False}
            self.events.append(event)

            def phase(name):
                event["phase"] = name
                event["phases"].append(name)

            try:
                phase("request_type_before")
                event["request_class"] = safe_type(request)
                phase("get_request_before")
                payload = request.getRequest()
                phase("get_request_after")
                event["payload_class"] = safe_type(payload)
                phase("classify_before")
                is_standard = isinstance(payload, DocumentPasswordRequest)
                is_ms = False if is_standard else isinstance(payload, DocumentMSPasswordRequest)
                event["is_document_password"] = is_standard
                event["is_document_ms_password"] = is_ms
                event["request_kind"] = "DocumentPasswordRequest" if is_standard else "DocumentMSPasswordRequest" if is_ms else "OTHER"
                is_error_code = not is_standard and not is_ms and ErrorCodeRequest2 is not None and type(payload) is ErrorCodeRequest2
                event["is_error_code_request2"] = is_error_code
                if is_error_code:
                    event["request_kind"] = "ErrorCodeRequest2"
                    phase("error_code_before")
                    error_code = payload.ErrCode
                    if type(error_code) is not int or not -(2**31) <= error_code < 2**31:
                        raise ValueError("typed_error_code_contract")
                    event["error_code"] = error_code
                    phase("error_code_after")
                phase("classify_after")
                phase("get_continuations_before")
                continuations = request.getContinuations()
                phase("get_continuations_after")
                event["continuation_attempts"] = []
                for continuation in continuations:
                    attempt = {"phase": "query_abort_type_before"}
                    event["continuation_attempts"].append(attempt)
                    phase("query_abort_type_before")
                    abort_type = uno.getTypeByName("com.sun.star.task.XInteractionAbort")
                    phase("query_interface_before")
                    attempt["phase"] = "query_interface_before"
                    abort = continuation.queryInterface(abort_type)
                    attempt["abort_available"] = abort is not None
                    attempt["phase"] = "query_interface_after"
                    phase("query_interface_after")
                    if abort is not None:
                        attempt["phase"] = "select_before"
                        phase("select_before")
                        abort.select()
                        event["abort_selected"] = True
                        attempt["phase"] = "select_after"
                        phase("select_after")
                        return
                phase("no_abort_continuation")
            except Exception as error:
                event["callback_error_phase"] = event["phase"]
                try:
                    event["callback_error"] = safe_exception(error)
                except Exception:
                    event["callback_error"] = {"exception_class": "DIAGNOSTIC_FAILURE", "source_frames": []}
                phase("callback_exception_reraised")
                raise

    return AbortInteractions()


def observed_password_abort(events):
    """Necessary event evidence only; caller must ALSO prove unopened load.

    No generic None/exception/ErrorCode/ArgumentPosition is password evidence.
    Requiring completed selection rejects callback failures and all other kinds.
    """
    return bool(events) and all(
        e.get("request_kind") in ("DocumentPasswordRequest", "DocumentMSPasswordRequest")
        and e.get("abort_selected") is True
        and e.get("phase") == "select_after"
        and "callback_error" not in e
        and "callback_error_phase" not in e
        for e in events
    )


# include/comphelper/errcode.hxx: Io=0, Abort=1, ERRCODE_IO_ABORT code27;
# ERRCODE_ABORT aliases it. ErrorCodeRequest2.ErrCode is IDL signed long.
EXPECTED_IO_ABORT = 283


def observed_password_refusal_sequence(events, fmt):
    """Necessary exact event order ONLY; unopened+same-byte positive required.

    Primary26.2 ODF abort emits one password Abort then one ErrorCodeRequest2
    carrying ERRCODE_IO_ABORT. Divergent types/codes/order, extra callbacks,
    incomplete selections and callback faults reject. Source verifier can mask
    internal IO/corruption as WrongPassword: this is cancellation evidence,
    not a cryptographic cause proof; same-byte correct semantics remain required.
    """
    if not isinstance(events, list):
        return False
    if fmt in ("docx", "xlsx", "pptx"):
        return len(events) == 1 and events[0].get("request_kind") == "DocumentMSPasswordRequest" and observed_password_abort(events)
    if fmt not in ("odt", "ods", "odp") or len(events) != 2:
        return False
    password, cancellation = events
    return (
        password.get("request_kind") == "DocumentPasswordRequest"
        and observed_password_abort([password])
        and cancellation.get("request_kind") == "ErrorCodeRequest2"
        and cancellation.get("payload_class") == "com.sun.star.task.ErrorCodeRequest2"
        and cancellation.get("is_error_code_request2") is True
        and type(cancellation.get("error_code")) is int
        and cancellation["error_code"] == EXPECTED_IO_ABORT
        and cancellation.get("abort_selected") is True
        and cancellation.get("phase") == "select_after"
        and "callback_error" not in cancellation
        and "callback_error_phase" not in cancellation
    )
