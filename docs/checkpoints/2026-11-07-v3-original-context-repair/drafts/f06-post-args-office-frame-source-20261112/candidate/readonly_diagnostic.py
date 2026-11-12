"""DORMANT adapter for one future Root-admitted missing bridge observation.

Not a frame, launcher, authority, password reader, oracle replacement or test
retry. Root supplies its already admitted empty Desktop, exact selected file
URL, in-memory correct synthetic password and existing semantic predicate.
The source alone authorizes NO execution. Imports no UNO and writes no files.
"""
from conversion_probe import OneShotConversionProbe, exception_metadata
from callback_observer_v2 import make_abort_handler


def observe_one_readonly(*, uno, unohelper, desktop, property_value,
                         interaction_handler_type, password_request_type,
                         ms_password_request_type, error_code_request_type,
                         compat_token, selected_file_url, correct_password,
                         semantic_check):
    if selected_file_url != "file:///inputs/native-outputs/retained-source.ott":
        raise ValueError("ROOT_BOUND_SELECTED_STAGED_FILE_URL_REQUIRED")
    if type(correct_password) is not str or not correct_password:
        raise ValueError("ROOT_IN_MEMORY_CORRECT_PASSWORD_REQUIRED")
    probe = OneShotConversionProbe(uno, compat_token)
    handler = make_abort_handler(uno, unohelper, interaction_handler_type,
                                 password_request_type, ms_password_request_type,
                                 error_code_request_type, request_probe=probe)
    properties = []
    for name, value in (("Hidden", True), ("ReadOnly", True), ("AsTemplate", False),
                        ("MacroExecutionMode", 0), ("UpdateDocMode", 0),
                        ("InteractionHandler", handler), ("Password", correct_password)):
        prop = property_value()
        prop.Name, prop.Value = name, value
        properties.append(prop)
    result = {"schema": "friday.f06.one-bridge-observation.v1",
              "state": "DIAGNOSTIC_NOT_QUALIFICATION", "load_calls": 0,
              "opened": False, "semantic_match": False,
              "close_attempted": False, "closed_or_disposed": False,
              "planned_stores": 0, "store_count_instrumented": False,
              "original_strict_all_pass": False,
              "acceptance_granted": False, "actual_payload_type": "UNKNOWN"}
    doc = None
    try:
        result["load_calls"] = 1
        doc = desktop.loadComponentFromURL(selected_file_url, "_blank", 0, tuple(properties))
        if doc is not None:
            result["opened"] = True
            result["semantic_match"] = bool(semantic_check(doc))
    except BaseException as error:
        result["load_or_semantic_error"] = exception_metadata(error)
    finally:
        result["interaction_events"] = handler.events
        if doc is not None:
            result["close_attempted"] = True
            try:
                doc.close(True)
                result["closed_or_disposed"] = True
            except BaseException as error:
                result["close_error"] = exception_metadata(error)
                try:
                    doc.dispose()
                    result["closed_or_disposed"] = True
                except BaseException as dispose_error:
                    result["dispose_error"] = exception_metadata(dispose_error)
    # No all_pass computation or benign-error classification. Root evaluates
    # captured diagnostics separately and must always close the private client.
    result["get_request_window_consumed"] = probe.used
    return result
