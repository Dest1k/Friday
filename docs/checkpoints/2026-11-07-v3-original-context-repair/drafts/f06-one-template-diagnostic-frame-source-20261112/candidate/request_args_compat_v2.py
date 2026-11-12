"""DORMANT, process-local compatibility for exactly four password exceptions and source-identified ErrorCodeRequest2.

No UNO imports, Office connection, global helper changes or acceptance rule.
Root may call install_request_args_compat(uno) in an admitted fresh client after
pinning the installed UNO sources and this file. Every non-args assignment still
uses the original UNO setter; Message/Name/password data are never inspected.
"""

REQUEST_NAMES = (
    "com.sun.star.task.DocumentPasswordRequest",
    "com.sun.star.task.DocumentMSPasswordRequest",
    "com.sun.star.task.DocumentPasswordRequest2",
    "com.sun.star.task.DocumentMSPasswordRequest2",
    "com.sun.star.task.ErrorCodeRequest2",
)


def _args_setter(original):
    def set_request_attribute(self, name, value):
        if name == "args":
            if type(value) is not tuple:
                raise TypeError("password_request_args_tuple_required")
            return BaseException.__setattr__(self, name, value)
        return original(self, name, value)
    return set_request_attribute


def install_request_args_compat(uno):
    """Validate all five exact generated classes before changing any one.

    Returned tuple is an in-memory restore token, never a JSON artifact. A fresh
    client exits after the bounded probe. Repeated installation is rejected.
    """
    original = uno._uno_struct__setattr__
    classes = tuple(uno.getClass(name) for name in REQUEST_NAMES)
    if len(set(classes)) != len(REQUEST_NAMES):
        raise ValueError("password_request_class_identity")
    for name, cls in zip(REQUEST_NAMES, classes):
        if type(cls) is not type or not issubclass(cls, Exception):
            raise ValueError("password_request_exception_class_required")
        if cls.__dict__.get("__pyunostruct__") != name:
            raise ValueError("password_request_exact_type_required")
        if cls.__dict__.get("__setattr__") is not original:
            raise ValueError("password_request_original_setter_required")
    token = tuple((cls, original, _args_setter(original)) for cls in classes)
    changed = []
    try:
        for cls, old_setter, replacement in token:
            cls.__setattr__ = replacement
            changed.append((cls, old_setter))
    except Exception:
        for cls, old_setter in reversed(changed):
            cls.__setattr__ = old_setter
        raise
    return token


def restore_request_args_compat(token):
    """CAS the entire token before restoring; never overwrite a later mutation."""
    if type(token) is not tuple or len(token) != len(REQUEST_NAMES):
        raise ValueError("password_request_restore_token")
    for name, row in zip(REQUEST_NAMES, token):
        if type(row) is not tuple or len(row) != 3:
            raise ValueError("password_request_restore_row")
        cls, original, replacement = row
        if type(cls) is not type or cls.__dict__.get("__pyunostruct__") != name:
            raise ValueError("password_request_restore_class")
        if cls.__dict__.get("__setattr__") is not replacement:
            raise ValueError("password_request_restore_cas")
    for cls, original, replacement in token:
        cls.__setattr__ = original
