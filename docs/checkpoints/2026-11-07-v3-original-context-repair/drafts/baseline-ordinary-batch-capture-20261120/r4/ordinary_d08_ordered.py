"""D08 composer for the existing owned caller and its exact two-phase plan."""

from hashlib import sha256
import os
from pathlib import Path
import re
import stat


TEMPLATE = "4179d32e059317d0b358f2be24788768d0f578a4dd31cc57d75de2c177cb9435"
FILL = "930b8a83367fdf599461a95b86697b9f827cef4756f5aff57b2fff6a1715b4e6"
COMPOSER_SHA256 = "57a21c19d5c2fde2ad06a9800502bdb7a5001ddf1be004c98c6ffe609bc139f6"


def compose_observer(source, *, run_id, scenario_sha256, authority, **references):
    """Require the exact settled template phase before composing the fill phase."""
    if type(run_id) is not str or scenario_sha256 not in (TEMPLATE, FILL) or type(authority) is not dict:
        raise ValueError("Exact D08 phase and authority required")
    bindings = authority.get("ordered_predecessors", {})
    if scenario_sha256 == TEMPLATE:
        if bindings != {}:
            raise ValueError("D08 template phase requires independent admission")
    else:
        predecessor = bindings.get(run_id) if type(bindings) is dict else None
        if (type(predecessor) is not dict
                or predecessor.get("scenario_sha256") != TEMPLATE
                or predecessor.get("initially_absent") is not False
                or type(predecessor.get("run_id")) is not str):
            raise ValueError("D08 fill requires the exact settled template predecessor")
        history = authority.get("history")
        retained = history.get(predecessor["run_id"]) if type(history) is dict else None
        pin = predecessor.get("run_record_sha256")
        review = predecessor.get("review")
        review_pin = review.get("sha256") if type(review) is dict else None
        if (type(retained) is not dict or retained.get("sha256") != pin
                or retained.get("status") != "EVIDENCE_READY" or retained.get("send_state") != "sent"
                or any(type(value) is not str or not re.fullmatch("[a-f0-9]{64}", value)
                       for value in (pin, review_pin))):
            raise ValueError("D08 fill requires the retained template run and independent review pins")

    path = Path(__file__).with_name("ordinary_admission_source.py")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_size > 65536:
            raise ValueError("Bounded regular ordinary admission composer required")
        raw = stream.read(65537)
    if sha256(raw).hexdigest() != COMPOSER_SHA256:
        raise ValueError("Exact reviewed ordinary admission composer required")
    namespace = {"__file__": str(path)}
    exec(compile(raw, str(path), "exec"), namespace)
    return namespace["compose_observer"](source, run_id=run_id, scenario_sha256=scenario_sha256,
                                         authority=authority, **references)
