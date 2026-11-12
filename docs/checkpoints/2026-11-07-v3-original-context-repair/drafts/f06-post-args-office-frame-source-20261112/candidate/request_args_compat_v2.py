"""DORMANT, process-local compatibility for exactly four password exceptions and ErrorCodeRequest2/ErrorCodeRequest.

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
    "com.sun.star.task.ErrorCodeRequest",
)


def _args_setter(original, expected_class):
    def set_request_attribute(self, name, value):
        if type(self) is expected_class and type(name) is str and name == "args":
            if type(value) is not tuple:
                raise TypeError("password_request_args_tuple_required")
            return BaseException.args.__set__(self, value)
        return original(self, name, value)
    return set_request_attribute


def install_request_args_compat(uno):
    """Validate all six exact generated classes before changing any one.

    Returned tuple is an in-memory restore token, never a JSON artifact. A fresh
    client exits after the bounded probe. Repeated installation is rejected.
    """
    original = uno._uno_struct__setattr__
    factory = uno.getClass
    factory_function = getattr(factory, "__func__", factory)
    factory_owner = getattr(factory, "__self__", None)
    classes = tuple(factory(name) for name in REQUEST_NAMES)
    if len(set(classes)) != len(REQUEST_NAMES):
        raise ValueError("password_request_class_identity")
    for name, cls in zip(REQUEST_NAMES, classes):
        if type(cls) is not type or not issubclass(cls, Exception):
            raise ValueError("password_request_exception_class_required")
        marker = cls.__dict__.get("__pyunostruct__")
        if type(marker) is not str or marker != name:
            raise ValueError("password_request_exact_type_required")
        if cls.__dict__.get("__setattr__") is not original:
            raise ValueError("password_request_original_setter_required")
    token = tuple((cls, original, _args_setter(original, cls)) for cls in classes)
    changed = []
    try:
        for name, (cls, old_setter, replacement) in zip(REQUEST_NAMES, token):
            current_factory = uno.getClass
            marker = cls.__dict__.get("__pyunostruct__")
            if (uno._uno_struct__setattr__ is not original
                    or getattr(current_factory, "__func__", current_factory) is not factory_function
                    or getattr(current_factory, "__self__", None) is not factory_owner
                    or type(marker) is not str or marker != name
                    or cls.__dict__.get("__setattr__") is not old_setter):
                raise ValueError("password_request_install_cas")
            cls.__setattr__ = replacement
            changed.append((cls, old_setter, replacement))
        current_factory = uno.getClass
        if (uno._uno_struct__setattr__ is not original
                or getattr(current_factory, "__func__", current_factory) is not factory_function
                or getattr(current_factory, "__self__", None) is not factory_owner):
            raise ValueError("password_request_install_cas")
        for name, (cls, old_setter, replacement) in zip(REQUEST_NAMES, token):
            marker = cls.__dict__.get("__pyunostruct__")
            if (type(marker) is not str or marker != name
                    or cls.__dict__.get("__setattr__") is not replacement):
                raise ValueError("password_request_install_cas")
    except BaseException:
        for cls, old_setter, replacement in reversed(changed):
            try:
                if cls.__dict__.get("__setattr__") is replacement:
                    cls.__setattr__ = old_setter
            except BaseException:
                # Preserve the primary error; the failed private client exits.
                pass
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
        if type(cls) is not type:
            raise ValueError("password_request_restore_class")
        marker = cls.__dict__.get("__pyunostruct__")
        if type(marker) is not str or marker != name:
            raise ValueError("password_request_restore_class")
        if cls.__dict__.get("__setattr__") is not replacement:
            raise ValueError("password_request_restore_cas")
    for cls, original, replacement in token:
        cls.__setattr__ = original
