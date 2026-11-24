"""Bounded file transfers for the TrueConf Server Chatbot API 5.5.4+.

The caller supplies an authenticated RPC function bound to one WebSocket
session and an HTTP client with the same TLS policy and no transport retries.
"""

from __future__ import annotations

import asyncio
import ipaddress
import json
import math
import mimetypes
import os
import re
import secrets
import stat
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import SplitResult, urlsplit

import httpx

DEFAULT_FILE_BYTES = 16 * 1024 * 1024
DEFAULT_TRANSFER_TIMEOUT = 30.0
_FILES_PATH = "/bridge/api/client/v1/files"
_CHUNK_SIZE = 64 * 1024
_UPLOAD_RESPONSE_LIMIT = 16 * 1024
_WIRE_ID = re.compile(r"[A-Za-z0-9_-]{1,256}")
_HOST_NAME = re.compile(r"[A-Za-z0-9.-]+")
Rpc = Callable[[str, dict[str, object]], Awaitable[Mapping[str, object]]]


class FileTransferError(Exception):
    """A safe error reason. Ambiguity refers to the temporary HTTP upload."""

    def __init__(self, reason: str, *, ambiguous: bool = False) -> None:
        super().__init__(reason)
        self.reason = reason
        self.ambiguous = ambiguous


class FileUploadCancelled(asyncio.CancelledError):
    """An external cancellation after attempting the temporary upload."""

    reason = "upload_cancelled"
    ambiguous = True


@dataclass(frozen=True)
class FileUploadLimits:
    max_size: int | None
    mode: str | None = None
    extensions: frozenset[str] = frozenset()

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> FileUploadLimits:
        if not isinstance(payload, Mapping) or "maxSize" not in payload or "extensions" not in payload:
            raise FileTransferError("invalid_upload_limits")
        max_size = payload["maxSize"]
        if max_size is not None and (type(max_size) is not int or not 0 <= max_size <= 2**32 - 1):
            raise FileTransferError("invalid_upload_limits")
        raw_extensions = payload["extensions"]
        if raw_extensions is None:
            return cls(max_size)
        if not isinstance(raw_extensions, dict):
            raise FileTransferError("invalid_upload_limits")
        mode = raw_extensions.get("mode")
        entries = raw_extensions.get("list")
        if mode not in ("allow", "block") or not isinstance(entries, list):
            raise FileTransferError("invalid_upload_limits")
        if any(
            not isinstance(entry, str)
            or not entry
            or any(c in "./\\" or c.isspace() or ord(c) < 32 for c in entry)
            for entry in entries
        ):
            raise FileTransferError("invalid_upload_limits")
        return cls(max_size, mode, frozenset(entry.lower() for entry in entries))

    def validate_name(self, name: str) -> None:
        extension = os.path.splitext(name)[1].removeprefix(".").lower()
        if (self.mode == "allow" and extension not in self.extensions) or (
            self.mode == "block" and extension in self.extensions
        ):
            raise FileTransferError("extension_disallowed")


def _wire_id(value: object, reason: str) -> str:
    if not isinstance(value, str) or not _WIRE_ID.fullmatch(value):
        raise FileTransferError(reason)
    return value


def _split_url(value: object) -> tuple[SplitResult, tuple[str, str, int]]:
    if (
        not isinstance(value, str)
        or not value
        or any(ord(c) < 33 or ord(c) > 126 or c in "\\?#" for c in value)
    ):
        raise FileTransferError("invalid_file_url")
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        port = parsed.port
    except ValueError:
        raise FileTransferError("invalid_file_url") from None

    if parsed.scheme not in ("https", "http") or not host or parsed.username is not None:
        raise FileTransferError("invalid_file_url")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is None and not _HOST_NAME.fullmatch(host):
        raise FileTransferError("invalid_file_url")
    if parsed.scheme == "http" and (address is None or not address.is_loopback):
        raise FileTransferError("insecure_file_origin")
    authority = f"[{host}]" if ":" in host else host
    if port is not None:
        authority += f":{port}"
    if port == 0 or parsed.netloc.lower() != authority:
        raise FileTransferError("invalid_file_url")
    return parsed, (parsed.scheme, host, port or (443 if parsed.scheme == "https" else 80))


def file_origin(origin: str) -> tuple[str, tuple[str, str, int]]:
    """Validate the configured origin and supply its normalized comparison key."""
    parsed, key = _split_url(origin)
    if parsed.path not in ("", "/"):
        raise FileTransferError("invalid_file_origin")
    scheme, host, port = key
    authority = f"[{host}]" if ":" in host else host
    default_port = 443 if scheme == "https" else 80
    if port != default_port:
        authority += f":{port}"
    return f"{scheme}://{authority}", key


def _validate_budget(max_bytes: int, timeout: float) -> None:
    if type(max_bytes) is not int or max_bytes < 0:
        raise FileTransferError("invalid_byte_limit")
    if type(timeout) not in (int, float) or not 0 < timeout < math.inf:
        raise FileTransferError("invalid_transfer_timeout")


def _read_upload(
    path: str | os.PathLike[str],
    max_bytes: int,
    limits: FileUploadLimits | None,
) -> tuple[str, bytes]:
    try:
        source = Path(path)
        name = source.name
        if not name or any(c in "\\" or ord(c) < 32 or ord(c) == 127 for c in name):
            raise FileTransferError("invalid_upload_name")
        name.encode("utf-8")
        if limits is not None:
            limits.validate_name(name)
            if limits.max_size is not None:
                max_bytes = min(max_bytes, limits.max_size)
        descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as stream:
            initial = os.fstat(stream.fileno())
            if not stat.S_ISREG(initial.st_mode):
                raise FileTransferError("invalid_upload_source")
            if not 0 <= initial.st_size <= max_bytes:
                raise FileTransferError("upload_too_large")

            body = stream.read(initial.st_size + 1)
            final = os.fstat(stream.fileno())
            if (
                len(body) != initial.st_size
                or final.st_size != initial.st_size
                or final.st_mtime_ns != initial.st_mtime_ns
                or final.st_ctime_ns != initial.st_ctime_ns
            ):
                raise FileTransferError("upload_source_changed")
            return name, body
    except (OSError, TypeError, ValueError):
        raise FileTransferError("invalid_upload_source") from None


def _validate_response_headers(
    response: httpx.Response,
    *,
    cap: int,
    expected: int | None = None,
    ambiguous: bool = False,
) -> None:
    encodings = [value.lower() for value in response.headers.get_list("content-encoding")]
    if encodings and encodings != ["identity"]:
        raise FileTransferError("unexpected_content_encoding", ambiguous=ambiguous)

    lengths = response.headers.get_list("content-length")
    if not lengths:
        return
    length = lengths[0]
    if (
        len(lengths) != 1
        or "transfer-encoding" in response.headers
        or len(length) > 20
        or not (length.isascii() and length.isdecimal())
    ):
        raise FileTransferError("invalid_content_length", ambiguous=ambiguous)
    declared = int(length)
    if declared > cap:
        raise FileTransferError("response_too_large", ambiguous=ambiguous)
    if expected is not None and declared != expected:
        raise FileTransferError("size_mismatch", ambiguous=ambiguous)


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    payload = dict(pairs)
    if len(payload) != len(pairs):
        raise ValueError("duplicate JSON key")
    return payload


async def _post_upload(http: httpx.AsyncClient, origin: str, task_id: str, name: str, body: bytes) -> str:
    mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
    request = httpx.Request(
        "POST",
        origin + _FILES_PATH,
        headers={
            "Upload-Task-Id": task_id,
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
        files={"file": (name, body, mime)},
    )
    response = await http.send(request, stream=True, auth=None, follow_redirects=False)
    try:
        if response.status_code != 200:
            raise FileTransferError(
                "upload_rejected" if response.status_code == 400 else "upload_http_status",
                ambiguous=response.status_code != 400,
            )
        content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            raise FileTransferError("invalid_upload_response", ambiguous=True)
        _validate_response_headers(response, cap=_UPLOAD_RESPONSE_LIMIT, ambiguous=True)
        content = bytearray()
        async for chunk in response.aiter_raw(chunk_size=_UPLOAD_RESPONSE_LIMIT + 1):
            if len(content) + len(chunk) > _UPLOAD_RESPONSE_LIMIT:
                raise FileTransferError("response_too_large", ambiguous=True)
            content.extend(chunk)
        try:
            payload = json.loads(content, object_pairs_hook=_unique_json_object)
            return _wire_id(payload["temporalFileId"], "invalid_upload_response")
        except (FileTransferError, TypeError, ValueError, KeyError, RecursionError):
            raise FileTransferError("invalid_upload_response", ambiguous=True) from None
    finally:
        await response.aclose()


async def upload_file(
    http: httpx.AsyncClient,
    origin: str,
    rpc: Rpc,
    path: str | os.PathLike[str],
    *,
    max_bytes: int = DEFAULT_FILE_BYTES,
    limits: FileUploadLimits | None = None,
    timeout: float = DEFAULT_TRANSFER_TIMEOUT,
    before_post=None,
) -> str:
    """Stage one local file and return its temporary ID for one sendFile RPC."""
    origin, _ = file_origin(origin)
    _validate_budget(max_bytes, timeout)
    posting = False
    try:
        async with asyncio.timeout(timeout):
            name, body = await asyncio.to_thread(_read_upload, path, max_bytes, limits)
            payload = await rpc("uploadFile", {"fileName": name, "fileSize": len(body)})
            if not isinstance(payload, Mapping):
                raise FileTransferError("invalid_upload_task_id")
            task_id = _wire_id(payload.get("uploadTaskId"), "invalid_upload_task_id")
            if http.is_closed:
                raise FileTransferError("upload_http_closed")
            if before_post is not None:
                before_post()
            posting = True
            return await _post_upload(http, origin, task_id, name, body)
    except TimeoutError:
        raise FileTransferError("upload_timeout", ambiguous=posting) from None
    except httpx.HTTPError:
        raise FileTransferError("upload_transport_error", ambiguous=posting) from None
    except RuntimeError:
        if not http.is_closed:
            raise
        raise FileTransferError("upload_http_closed", ambiguous=posting) from None
    except asyncio.CancelledError:
        if posting:
            raise FileUploadCancelled("upload_cancelled") from None
        raise


async def _save_download(response: httpx.Response, target: Path, expected: int) -> None:
    # Pin the directory and publish with an exclusive link after the byte count
    # is verified, so concurrent writers and preexisting targets are preserved.
    directory = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    temporary_name = ".trueconf-" + secrets.token_hex(16)
    published = False
    try:
        descriptor = os.open(
            temporary_name,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory,
        )
        try:
            received = 0
            with os.fdopen(descriptor, "wb") as stream:
                async for chunk in response.aiter_raw(chunk_size=min(expected + 1, _CHUNK_SIZE)):
                    received += len(chunk)
                    if received > expected:
                        raise FileTransferError("size_mismatch")
                    stream.write(chunk)
                if received != expected:
                    raise FileTransferError("size_mismatch")
            os.link(
                temporary_name,
                target.name,
                src_dir_fd=directory,
                dst_dir_fd=directory,
                follow_symlinks=False,
            )
            published = True
        finally:
            try:
                os.unlink(temporary_name, dir_fd=directory)
            except OSError:
                reason = "download_published_cleanup_error" if published else "download_cleanup_error"
                raise FileTransferError(reason) from None
    finally:
        try:
            os.close(directory)
        except OSError:
            if published:
                raise FileTransferError("download_published_cleanup_error") from None
            raise


async def download_file(
    http: httpx.AsyncClient,
    origin: str,
    rpc: Rpc,
    file_id: str,
    target: str | os.PathLike[str],
    *,
    max_bytes: int = DEFAULT_FILE_BYTES,
    expected_size: int | None = None,
    timeout: float = DEFAULT_TRANSFER_TIMEOUT,
) -> Path:
    """Download a READY original file to an unoccupied caller-selected path."""
    origin, origin_key = file_origin(origin)
    file_id = _wire_id(file_id, "invalid_file_id")
    _validate_budget(max_bytes, timeout)
    if expected_size is not None and (type(expected_size) is not int or not 0 <= expected_size <= max_bytes):
        raise FileTransferError("invalid_expected_size")
    try:
        target = Path(target)
        if not target.name or target.name == ".." or target.is_symlink() or target.exists():
            raise FileTransferError("invalid_download_target")
    except (OSError, TypeError, ValueError):
        raise FileTransferError("invalid_download_target") from None

    try:
        async with asyncio.timeout(timeout):
            payload = await rpc("getFileInfo", {"fileId": file_id})
            if not isinstance(payload, Mapping) or payload.get("fileId") != file_id:
                raise FileTransferError("file_id_mismatch")
            state = payload.get("readyState")
            if type(state) is not int or state != 2:
                raise FileTransferError("file_not_ready")
            size = payload.get("size")
            if type(size) is not int or size < 0:
                raise FileTransferError("invalid_file_size")
            if size > max_bytes:
                raise FileTransferError("download_too_large")
            if expected_size is not None and size != expected_size:
                raise FileTransferError("size_mismatch")
            download_url, download_key = _split_url(payload.get("downloadUrl"))
            path = f"{_FILES_PATH}/{file_id}"
            if download_key != origin_key or download_url.path != path:
                raise FileTransferError("invalid_download_route")

            request = httpx.Request(
                "GET",
                origin + path,
                headers={"Accept-Encoding": "identity", "Connection": "close"},
            )
            response = await http.send(request, stream=True, auth=None, follow_redirects=False)
            try:
                if response.status_code != 200:
                    raise FileTransferError("download_http_status")
                _validate_response_headers(response, cap=max_bytes, expected=size)
                await _save_download(response, target, size)
            finally:
                await response.aclose()
    except TimeoutError:
        raise FileTransferError("download_timeout") from None
    except httpx.HTTPError:
        raise FileTransferError("download_transport_error") from None
    except RuntimeError:
        if not http.is_closed:
            raise
        raise FileTransferError("download_http_closed") from None
    except (OSError, ValueError):
        raise FileTransferError("download_target_error") from None
    return target
