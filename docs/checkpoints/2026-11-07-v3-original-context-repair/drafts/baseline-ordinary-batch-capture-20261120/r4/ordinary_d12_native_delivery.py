"""Read the selected D12 delivery and its exact producer journals from native storage."""

from hashlib import sha256
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import time


KEY = "ordinary_documents.v1"
ATTEMPT = "friday.ordinary-document-attempt.v1"


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


def selected_rows(index, selection, route, relative_path):
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
            or PurePosixPath(name).suffix.lower() != ".zip"
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


def read_selected_delivery(profile_home, *, route, relative_path, cutoff):
    """Read one point-in-time result for a previously authenticated native route.

    The caller binds the actual ingress and runtime profile directory. Use the
    returned records with the independent recipient check. This read cannot
    recover the original writer's commit-return witness.
    """
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
            check_deadline(cutoff)
            rows = selected_rows(state.get_storage_readonly(KEY, lock_deadline=cutoff), selection, frozen, relative_path)
            journals = {}
            for label in ("attempt", "reservation", "candidate"):
                check_deadline(cutoff)
                kind = "candidate" if label == "candidate" else "unknown"
                journals[label] = read_journal(dirfd, kind, encoded(rows[label]))
            named = directory_signature(os.stat(directory, follow_symlinks=False))
            if before != named or named != directory_signature(os.fstat(dirfd)):
                raise ValueError("D12 native storage directory changed")
        finally:
            os.close(dirfd)
    check_deadline(cutoff)
    return {"records": rows, "journal_references": journals, "writer_return": "UNESTABLISHED_BY_READBACK"}
