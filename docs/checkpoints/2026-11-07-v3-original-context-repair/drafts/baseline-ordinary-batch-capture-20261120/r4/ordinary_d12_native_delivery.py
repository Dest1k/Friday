"""Read selected D12 ZIP or D14 XLSX delivery evidence from native storage."""

from hashlib import sha256
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import time


KEY = "ordinary_documents.v1"
ATTEMPT = "friday.ordinary-document-attempt.v1"
OUTCOME = "friday.ordinary-document-outcome.v1"
OUTCOME_STATES = ("PENDING", "CONFIRMED", "FAILED", "UNKNOWN")


def check_deadline(cutoff):
    if type(cutoff) not in (int, float) or not math.isfinite(cutoff) or time.monotonic() >= cutoff:
        raise ValueError("D12 native evidence read deadline expired")


def read_journal(dirfd, kind, expected):
    from hermes_cli.friday_native_state import MAX_JOURNAL

    if not 0 < len(expected) <= MAX_JOURNAL:
        raise ValueError("D12 native journal size invalid")
    pin = sha256(expected).hexdigest()
    name = f"friday-{kind}-{pin}.json"
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
    with os.fdopen(os.open(name, flags, dir_fd=dirfd), "rb") as stream:
        def signature(info):
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1
                    or stat.S_IMODE(info.st_mode) != 0o400 or info.st_size != len(expected)):
                raise ValueError("D12 native journal custody invalid")
            return info.st_dev, info.st_ino, info.st_mtime_ns, info.st_ctime_ns

        before = signature(os.fstat(stream.fileno()))
        actual = stream.read(len(expected) + 1)
        after = signature(os.fstat(stream.fileno()))
        named = signature(os.stat(name, dir_fd=dirfd, follow_symlinks=False))
        if before != after or after != named or actual != expected:
            raise ValueError("D12 native journal bytes or identity changed")
    return {"name": name, "bytes": len(expected), "sha256": pin}


def selected_rows(index, selection, route, relative_path, *, suffix=".zip"):
    if (type(index) is not dict or set(index) != {"schema", "files"}
            or index["schema"] != KEY or type(index["files"]) is not dict):
        raise ValueError("D12 native delivery index unavailable")
    row = index["files"].get(selection)
    fields = {"state", "relative_path", "sha256", "bytes", "file_name", "route", "receipt"}
    if (type(row) is not dict or set(row) != fields or row["state"] != "DELIVERED"
            or row["route"] != route or row["relative_path"] != relative_path):
        raise ValueError("D12 selected native row is not the expected DELIVERED record")
    receipt = row["receipt"]
    name = row["file_name"]
    if (type(row["sha256"]) is not str or not re.fullmatch("[a-f0-9]{64}", row["sha256"])
            or type(row["bytes"]) is not int or not 0 < row["bytes"] <= 1_000_000
            or type(name) is not str or not 0 < len(name) <= 255
            or PurePosixPath(name).suffix.lower() != suffix
            or any(ord(char) < 32 or char in "/\\" for char in name)):
        raise ValueError("D12 selected native archive identity invalid")
    source = route["source"]
    expected = {
        "state": "DELIVERED", "kind": "document", "sha256": row["sha256"], "bytes": row["bytes"],
        "file_name": name, "bot_id": route["bot_id"], "chat_id": source["chat_id"],
        "thread_id": None, "reply_to": source["message_id"],
    }
    if (type(receipt) is not dict or set(receipt) != set(expected) | {"message_id"}
            or any(type(receipt[key]) is not type(value) or receipt[key] != value for key, value in expected.items())
            or type(receipt["message_id"]) is not str or not re.fullmatch("[1-9][0-9]*", receipt["message_id"])):
        raise ValueError("D12 selected native document receipt invalid")
    attempt = {"schema": ATTEMPT, "selection": selection, "route": route}
    reservation = {
        "state": "UNKNOWN", "relative_path": relative_path, "sha256": row["sha256"], "bytes": row["bytes"],
        "file_name": name, "route": route, "receipt": None,
    }
    candidate = {"selection": selection, "receipt": dict(expected, message_id=receipt["message_id"])}
    return {"attempt": attempt, "reservation": reservation, "candidate": candidate, "delivery": row}


def directory_signature(info):
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o700):
        raise ValueError("D12 native storage directory custody invalid")
    return info.st_dev, info.st_ino, info.st_mtime_ns, info.st_ctime_ns


def selected_outcome(index, dirfd, *, key, route, cutoff, encoded):
    """Read only the failure-status outcome for this path and ingress."""
    outcomes = index.get("outcomes", {})
    pending = {"schema": OUTCOME, "outcome_id": key, "route": route, "state": "PENDING"}
    reference = {}
    if key not in outcomes:
        check_deadline(cutoff)
        try:
            reference["pending"] = read_journal(dirfd, "unknown", encoded(pending))
        except FileNotFoundError:
            pass
        status = "PENDING_JOURNAL_WITHOUT_INDEX_ROW" if reference else "NO_SELECTED_OUTCOME_OBSERVED"
        return {"key": key, "status": status, "record": None, "journal_references": reference}

    row = outcomes[key]
    if (type(row) is not dict or set(row) != {"state", "route"} or row["route"] != route
            or row["state"] not in OUTCOME_STATES):
        raise ValueError("D14 selected native outcome differs from the exact route or state")
    check_deadline(cutoff)
    reference["pending"] = read_journal(dirfd, "unknown", encoded(pending))
    if row["state"] != "PENDING":
        check_deadline(cutoff)
        reference["settled"] = read_journal(dirfd, "candidate", encoded(dict(pending, state=row["state"])))
    return {"key": key, "status": "SELECTED_FAILURE_STATUS_NOTICE", "record": row,
            "journal_references": reference}


def state_signature(dirfd):
    signature = []
    for name in ("state.json", ".state.json.lock"):
        info = os.stat(name, dir_fd=dirfd, follow_symlinks=False)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1
                or stat.S_IMODE(info.st_mode) != 0o600):
            raise PermissionError("D14 native state or lock custody invalid")
        signature.append((info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns))
    return tuple(signature)


def read_selected_delivery(profile_home, *, route, relative_path, cutoff):
    """Read one point-in-time result for a previously authenticated native route.

    The caller binds the actual ingress and runtime profile directory. Use the
    returned records with the independent recipient check. This read cannot
    recover the original writer's commit-return witness.
    """
    return _read_selected_delivery(profile_home, route=route, relative_path=relative_path, cutoff=cutoff)


def read_selected_xlsx_delivery(profile_home, *, route, relative_path, artifact, cutoff, expected_outcome=None):
    """Read the D14 result for an authenticated route and externally verified XLSX identity."""
    if (type(artifact) is not dict or set(artifact) != {"sha256", "bytes", "file_name"}
            or type(artifact["sha256"]) is not str or not re.fullmatch("[a-f0-9]{64}", artifact["sha256"])
            or type(artifact["bytes"]) is not int or not 0 < artifact["bytes"] <= 1_000_000
            or type(artifact["file_name"]) is not str or PurePosixPath(artifact["file_name"]).suffix.lower() != ".xlsx"):
        raise ValueError("D14 exact XLSX artifact identity required")
    if expected_outcome is not None and expected_outcome not in OUTCOME_STATES:
        raise ValueError("D14 expected outcome state invalid")
    return _read_selected_delivery(profile_home, route=route, relative_path=relative_path, cutoff=cutoff,
                                   artifact=artifact, expected_outcome=expected_outcome)


def _read_selected_delivery(profile_home, *, route, relative_path, cutoff, artifact=None, expected_outcome=None):
    from gateway.run_plugin_delivery import freeze_route
    from hermes_cli.friday_native_state import encoded
    from hermes_cli.friday_product_access import principal_id
    from hermes_cli.friday_user_scope import authority
    from hermes_cli.plugins_state import PluginState

    check_deadline(cutoff)
    frozen = freeze_route(route)
    source = frozen["source"]
    profile = frozen["runtime_profile"]
    home = Path(profile_home)
    path = PurePosixPath(relative_path) if isinstance(relative_path, str) else PurePosixPath()
    if (frozen != route or source["chat_type"] != "dm" or source["chat_id"] != source["user_id"]
            or source["thread_id"] is not None or profile != "telegram-bot-" + source["user_id"]
            or not home.is_absolute() or home.resolve(strict=True) != home
            or home.name != profile or home.parent.name != "profiles"):
        raise ValueError("D12 authenticated native profile and unthreaded source required")
    if (not path.parts or path.is_absolute() or path.as_posix() != relative_path
            or any(part.startswith(".") for part in path.parts) or "\x00" in relative_path):
        raise ValueError("D12 exact relative workspace archive path required")
    if artifact is not None and (path.suffix.lower() != ".xlsx" or "\\" in relative_path):
        raise ValueError("D14 exact relative workspace XLSX path required")
    principal = principal_id(source["platform"], frozen["transport_profile"], frozen["bot_id"], source["user_id"])
    selection = sha256(encoded([principal, relative_path])).hexdigest()
    with authority(home):
        state = PluginState("friday_rework")
        directory = state.directory_storage_readonly
        if directory.parent != home / "plugin-data":
            raise ValueError("D12 native storage namespace changed")
        dirfd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            before = directory_signature(os.fstat(dirfd))
            state_before = state_signature(dirfd) if artifact is not None else None
            check_deadline(cutoff)
            index = state.get_storage_readonly(KEY, lock_deadline=cutoff)
            if artifact is None:
                rows = selected_rows(index, selection, frozen, relative_path)
            else:
                if (type(index) is not dict or set(index) not in ({"schema", "files"}, {"schema", "files", "outcomes"})
                        or type(index["files"]) is not dict or len(index["files"]) > 10_000
                        or type(index.get("outcomes", {})) is not dict or len(index.get("outcomes", {})) > 10_000):
                    raise ValueError("D14 native delivery or outcome index unavailable")
                documents = {key: index[key] for key in ("schema", "files")}
                rows = selected_rows(documents, selection, frozen, relative_path, suffix=".xlsx")
                if any(rows["delivery"][key] != value for key, value in artifact.items()):
                    raise ValueError("D14 selected delivery differs from the verified XLSX artifact")
            journals = {}
            for label in ("attempt", "reservation", "candidate"):
                check_deadline(cutoff)
                kind = "candidate" if label == "candidate" else "unknown"
                journals[label] = read_journal(dirfd, kind, encoded(rows[label]))
            if artifact is not None:
                outcome_key = sha256(encoded([principal, str(home / "workspace" / path), frozen])).hexdigest()
                outcome = selected_outcome(index, dirfd, key=outcome_key, route=frozen, cutoff=cutoff, encoded=encoded)
                if outcome["status"] == "PENDING_JOURNAL_WITHOUT_INDEX_ROW":
                    raise ValueError("D14 selected outcome pending journal exists without its index row")
                if (outcome["record"] or {}).get("state") != expected_outcome:
                    raise ValueError("D14 selected native outcome does not equal the expected state")
                if state_signature(dirfd) != state_before:
                    raise ValueError("D14 native state or lock changed during delivery observation")
            named = directory_signature(os.stat(directory, follow_symlinks=False))
            if before != named or named != directory_signature(os.fstat(dirfd)):
                raise ValueError("D12 native storage directory changed")
        finally:
            os.close(dirfd)
    check_deadline(cutoff)
    if artifact is not None:
        return {
            "index": {"schema": KEY, "files": {selection: rows["delivery"]}},
            "journals": {"attempt": rows["attempt"], "unknown": rows["reservation"], "candidate": rows["candidate"]},
            "journal_references": {"attempt": journals["attempt"], "unknown": journals["reservation"],
                                   "candidate": journals["candidate"]},
            "outcome": outcome, "writer_return": "UNESTABLISHED_BY_READBACK",
        }
    return {"records": rows, "journal_references": journals, "writer_return": "UNESTABLISHED_BY_READBACK"}
