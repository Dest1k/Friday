"""Bounded async transport for the documented TrueConf Chatbot API."""
from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import ssl
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, cast

import httpx
from websockets.asyncio.client import ClientConnection
from websockets.asyncio.client import connect as websocket_connect
from websockets.exceptions import ConnectionClosed, WebSocketException
from websockets.typing import Origin, Subprotocol

from .trueconf_files import (
    DEFAULT_FILE_BYTES,
    FileTransferError,
    download_file,
    file_origin,
    upload_file,
)

_MAX_ID = 2**32 - 1
_MAX_FRAME = 1024 * 1024
_MAX_TOKEN_BODY = 16 * 1024
_REJECTION_CODES = frozenset({
    2, 200, 201, 202, 203, 204, 302, 303, 304, 305, 306, 308, 311, 399,
    401, 402, 403, 404, 405, 406, 407, 408,
})
# Keep wire payloads out of ambient DEBUG logs without changing global logging.
_WS_LOGGER = logging.Logger("trueconf.websocket", level=logging.CRITICAL + 1)  # noqa: LOG001


class TrueConfError(Exception):
    """Sanitized transport failure. Ambiguous means a request may have reached the peer."""

    def __init__(self, reason: str, *, ambiguous: bool = False, error_code: int | None = None):
        super().__init__(reason)
        self.reason = reason
        self.ambiguous = ambiguous
        self.error_code = error_code


class TrueConfRequestCancelled(asyncio.CancelledError):
    """The cancelled request crossed the WebSocket submission boundary."""

    def __init__(self, method: str):
        super().__init__("request_cancelled_after_submit")
        self.method = method
        self.ambiguous = True


@dataclass(frozen=True, slots=True, repr=False)
class AccessToken:
    value: str
    expires_at: float


@dataclass(frozen=True, slots=True)
class Attachment:
    file_id: str | None
    name: str | None
    size: int | None
    kind: str
    mime_type: str | None


@dataclass(frozen=True, slots=True)
class MessageEvent:
    message_id: str | None
    chat_id: str | None
    sender_id: str | None
    chat_kind: str | None
    text: str | None
    reply_id: str | None
    attachments: tuple[Attachment, ...]
    timestamp: int | None
    sender_type: int | None
    message_type: int | None
    parse_mode: str | None


@dataclass(frozen=True, slots=True)
class IngressKey:
    origin: str
    account_id: str
    chat_id: str
    message_id: str


@dataclass(frozen=True, slots=True)
class IngressReceipt:
    key: IngressKey
    status: Literal["NEW", "DUPLICATE", "DISCARDED"]


class IngressAckError(TrueConfError):
    """Persistence succeeded, but the notification ACK could not be confirmed locally."""

    def __init__(self, receipt: IngressReceipt, *, ambiguous: bool):
        super().__init__("ingress_ack_unavailable", ambiguous=ambiguous)
        self.receipt = receipt


class IngressAckCancelled(asyncio.CancelledError):
    """Cancellation after the callback returned its durable handoff receipt."""

    def __init__(self, receipt: IngressReceipt):
        super().__init__("ingress_cancelled_after_receipt")
        self.receipt = receipt


@dataclass(frozen=True, slots=True)
class IngressDelivery:
    event: MessageEvent = field(repr=False)
    key: IngressKey
    _accept: Callable[
        [Callable[[IngressKey], Awaitable[IngressReceipt]]], Awaitable[IngressReceipt]
    ] = field(repr=False, compare=False)

    async def accept(
        self, persist: Callable[[IngressKey], Awaitable[IngressReceipt]]
    ) -> IngressReceipt:
        """Commit or match this handoff before acknowledging its original notification."""
        return await self._accept(persist)


@dataclass(frozen=True, slots=True)
class SendResult:
    status: str
    message_id: str | None = None
    file_id: str | None = None
    reason: str | None = None
    error_code: int | None = None
    timestamp: int | None = None


def _uint(value: object, upper: int = 2**64 - 1) -> int | None:
    return value if type(value) is int and 0 <= value <= upper else None


def _identifier(value: object) -> str | None:
    if isinstance(value, str) and 0 < len(value) <= 1024 and not any(
        char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value
    ):
        return value
    return None


def _require_id(value: object, reason: str) -> str:
    result = _identifier(value)
    if result is None:
        raise TrueConfError(reason)
    return result


def _text(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _object(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _join_id(left: object, right: object, reason: str) -> str | None:
    a, b = _identifier(left), _identifier(right)
    if (left is not None and a is None) or (right is not None and b is None) or (a and b and a != b):
        raise TrueConfError(reason)
    return a or b


def _message(value: object) -> MessageEvent:
    if not isinstance(value, dict):
        raise TrueConfError("invalid_message")
    chat = _object(value.get("chat"))
    author = _object(value.get("author"))
    content = _object(value.get("content"))
    reply = _object(value.get("replyMessage"))
    message_type = _uint(value.get("type"))
    chat_type = _uint(chat.get("chatType"))
    if chat_type is None:
        chat_type = _uint(value.get("chatType"))
    attachments: tuple[Attachment, ...] = ()
    if message_type in (202, 205):
        attachments = (Attachment(
            _identifier(content.get("fileId")), _text(content.get("name")), _uint(content.get("size")),
            "voice" if message_type == 205 else "file", _text(content.get("mimeType")),
        ),)
    return MessageEvent(
        _identifier(value.get("messageId")),
        _join_id(chat.get("chatId"), value.get("chatId"), "invalid_chat_route"),
        _identifier(author.get("id")),
        {1: "direct", 2: "group"}.get(chat_type) if chat_type is not None else None,
        _text(content.get("text")) if message_type == 200 else _text(content.get("caption")) if attachments else None,
        _join_id(value.get("replyMessageId"), reply.get("messageId"), "invalid_reply_identity"),
        attachments,
        _uint(value.get("timestamp")),
        _uint(author.get("type")),
        message_type,
        _text(content.get("parseMode")) if message_type == 200 else None,
    )


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise ValueError("nonfinite constant")


def _parse_json(data: str | bytes) -> object:
    return json.loads(data, object_pairs_hook=_unique_object, parse_constant=_reject_constant)


def _origin(value: str, allow_loopback_http: bool) -> tuple[str, str]:
    try:
        origin, (scheme, _, _) = file_origin(value)
    except FileTransferError:
        raise ValueError("invalid TrueConf origin") from None
    if scheme == "http" and not allow_loopback_http:
        raise ValueError("TrueConf requires verified HTTPS")
    ws_scheme = "wss" if scheme == "https" else "ws"
    authority = origin.split("://", 1)[1]
    return origin, f"{ws_scheme}://{authority}/websocket/chat_bot/"


class _NoRedirectConnect(websocket_connect):
    def process_redirect(self, exc: Exception) -> Exception:
        return exc


@dataclass(slots=True)
class _Session:
    websocket: ClientConnection
    queue: asyncio.Queue[MessageEvent | IngressDelivery | str | None]
    event_limit: int
    unread_requested: bool
    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    auth_done: asyncio.Event = field(default_factory=asyncio.Event)
    pending: dict[int, asyncio.Future] = field(default_factory=dict)
    unacknowledged_ingress: set[int] = field(default_factory=set)
    next_id: int = 1
    reader: asyncio.Task | None = None
    ended: bool = False
    local_close: bool = False
    consuming: bool = False
    user_id: str | None = None


class TrueConfClient:
    def __init__(
        self,
        base_url: str,
        *,
        username: str | None = None,
        password: str | None = None,
        token_provider: Callable[[], Awaitable[AccessToken]] | None = None,
        expected_user_id: str | None = None,
        ssl_context: ssl.SSLContext | None = None,
        allow_loopback_http: bool = False,
        request_timeout: float = 5.0,
        event_limit: int = 128,
        max_upload_bytes: int = DEFAULT_FILE_BYTES,
        durable_ingress: bool = False,
    ):
        self._origin, self._ws_url = _origin(base_url, allow_loopback_http)
        if token_provider is None:
            if not isinstance(username, str) or not username or not isinstance(password, str) or not password:
                raise ValueError("provide a username and password or a token provider")
        elif username is not None or password is not None or not callable(token_provider):
            raise ValueError("provide one credential source")
        if expected_user_id is not None and _identifier(expected_user_id) is None:
            raise ValueError("invalid expected user ID")
        if type(durable_ingress) is not bool or (durable_ingress and expected_user_id is None):
            raise ValueError("durable ingress requires an exact expected user ID")
        if not math.isfinite(request_timeout) or request_timeout <= 0:
            raise ValueError("invalid request timeout")
        if type(event_limit) is not int or not 1 <= event_limit <= 4096:
            raise ValueError("invalid event queue limit")
        if type(max_upload_bytes) is not int or max_upload_bytes <= 0:
            raise ValueError("invalid upload byte limit")
        self._ssl = ssl.create_default_context() if ssl_context is None else ssl_context
        self._verify_tls()
        self._username = username
        self._password = password
        self._provider = token_provider
        self._expected_user = expected_user_id
        self._timeout = request_timeout
        self._event_limit = event_limit
        self._durable_ingress = durable_ingress
        self._max_upload_bytes = max_upload_bytes
        self._token: AccessToken | None = None
        self._lifecycle = asyncio.Lock()
        self._session: _Session | None = None
        self._http: httpx.AsyncClient | None = None

    def _verify_tls(self) -> None:
        if self._ssl.verify_mode != ssl.CERT_REQUIRED or not self._ssl.check_hostname:
            raise ValueError("TrueConf requires certificate and hostname verification")

    @property
    def origin(self) -> str:
        return self._origin

    @property
    def expected_user_id(self) -> str | None:
        return self._expected_user

    @property
    def unread_requested(self) -> bool | None:
        session = self._session
        return session.unread_requested if self.user_id is not None and session is not None else None

    @property
    def user_id(self) -> str | None:
        session = self._session
        return session.user_id if session and not session.ended else None

    def _http_client(self) -> httpx.AsyncClient:
        if self._http is None:
            raise TrueConfError("not_connected")
        return self._http

    async def _password_token(self) -> AccessToken:
        async with self._http_client().stream(
            "POST",
            self._origin + "/bridge/api/client/v1/oauth/token",
            json={
                "client_id": "chat_bot", "grant_type": "password",
                "username": self._username, "password": self._password,
            },
        ) as response:
            if response.status_code != 201:
                raise TrueConfError("token_http_status")
            if response.headers.get("content-encoding", "identity").lower() != "identity":
                raise TrueConfError("invalid_token_encoding")
            content = bytearray()
            async for chunk in response.aiter_raw():
                if len(content) + len(chunk) > _MAX_TOKEN_BODY:
                    raise TrueConfError("token_body_too_large")
                content.extend(chunk)
        payload = _object(_parse_json(bytes(content)))
        if payload.get("token_type") != "JWT":
            raise TrueConfError("invalid_token_type")
        value, expires_at = payload.get("access_token"), payload.get("expires_at")
        if not isinstance(value, str) or not isinstance(expires_at, (int, float)) or isinstance(expires_at, bool):
            raise TrueConfError("invalid_access_token")
        return AccessToken(value, expires_at)

    async def _get_token(self, *, force: bool) -> AccessToken:
        if not force and self._token and self._token.expires_at > time.time() + 1:
            return self._token
        try:
            operation = self._provider() if self._provider is not None else self._password_token()
            token = await asyncio.wait_for(operation, self._timeout)
            if (
                not isinstance(token, AccessToken) or not isinstance(token.value, str)
                or not 0 < len(token.value) <= _MAX_TOKEN_BODY
                or any(not 33 <= ord(char) <= 126 for char in token.value)
                or type(token.expires_at) not in (int, float) or not math.isfinite(token.expires_at)
                or token.expires_at <= time.time()
            ):
                raise TrueConfError("invalid_access_token")
        except TrueConfError:
            if self._provider is None:
                raise
            raise TrueConfError("token_provider_failed") from None
        except Exception:  # noqa: BLE001 - user token providers may raise arbitrary credential-bearing errors
            raise TrueConfError("token_acquisition_failed") from None
        self._token = token
        return token

    async def _shutdown(self, session: _Session) -> None:
        session.local_close = True
        session.auth_done.set()
        try:
            await session.websocket.close()
        finally:
            if session.reader is not None:
                await session.reader

    async def _open(self, *, force: bool, receive_unread: bool) -> str:
        self._verify_tls()
        if self._http is None:
            self._http = httpx.AsyncClient(
                verify=self._ssl, trust_env=False, follow_redirects=False,
                timeout=self._timeout, headers={"Accept-Encoding": "identity"},
            )
        for attempt in range(2):
            token = await self._get_token(force=force or bool(attempt))
            tls: dict[str, Any] = {"ssl": self._ssl} if self._ws_url.startswith("wss:") else {}
            try:
                socket = await _NoRedirectConnect(
                    self._ws_url, origin=Origin(self._origin), subprotocols=[Subprotocol("json.v1")], proxy=None,
                    compression=None, max_size=_MAX_FRAME, max_queue=16, open_timeout=self._timeout,
                    close_timeout=min(2.0, self._timeout), logger=_WS_LOGGER, **tls,
                )
            except (WebSocketException, OSError, TimeoutError, ValueError):
                raise TrueConfError("websocket_open_failed") from None
            session = _Session(socket, asyncio.Queue(self._event_limit + 1), self._event_limit, receive_unread)
            session.reader = asyncio.create_task(self._reader(session))
            keep = False
            try:
                if socket.subprotocol != "json.v1":
                    raise TrueConfError("invalid_websocket_subprotocol")
                payload = await self._request(
                    session, "auth", {"token": token.value, "tokenType": "JWT", "receiveUnread": receive_unread}
                )
                user_id = _require_id(_object(payload).get("userId"), "invalid_auth_identity")
                if self._expected_user is not None and user_id != self._expected_user:
                    raise TrueConfError("unexpected_auth_identity")
                if session.ended:
                    raise TrueConfError("websocket_disconnected")
                session.user_id = user_id
                self._session = session
                session.auth_done.set()
                keep = True
                return user_id
            except TrueConfError as exc:
                if exc.error_code != 203 or attempt:
                    raise
                self._token = None
            finally:
                if not keep:
                    await self._shutdown(session)
        raise TrueConfError("authentication_failed")

    def _require_unread_mode(self, receive_unread: bool) -> None:
        if type(receive_unread) is not bool or (receive_unread and not self._durable_ingress):
            raise TrueConfError("unread_requires_durable_ingress")

    async def connect(self, *, receive_unread: bool = False) -> str:
        self._require_unread_mode(receive_unread)
        async with self._lifecycle:
            session = self._session
            if session is not None and not session.ended and session.user_id is not None:
                if receive_unread and not session.unread_requested:
                    raise TrueConfError("unread_requires_reconnect")
                return session.user_id
            old, self._session = self._session, None
            if old is not None:
                await self._shutdown(old)
            return await self._open(force=False, receive_unread=receive_unread)

    async def reconnect(self, *, receive_unread: bool = False) -> str:
        self._require_unread_mode(receive_unread)
        async with self._lifecycle:
            old, self._session = self._session, None
            if old is not None:
                await self._shutdown(old)
            return await self._open(force=True, receive_unread=receive_unread)

    async def close(self) -> None:
        async with self._lifecycle:
            session, self._session = self._session, None
            http, self._http = self._http, None
            self._token = None
            try:
                if session is not None:
                    await self._shutdown(session)
            finally:
                if http is not None:
                    await http.aclose()

    def _active(self) -> _Session:
        session = self._session
        if session is None or session.local_close or session.ended or session.user_id is None:
            raise TrueConfError("not_connected")
        return session

    @staticmethod
    async def _wire_send(session: _Session, data: str) -> None:
        await session.websocket.send(data)

    def _ingress_session_current(self, session: _Session) -> bool:
        return self._session is session and not session.ended and not session.local_close

    def _make_delivery(self, session: _Session, msg_id: int, event: MessageEvent) -> IngressDelivery:
        if not session.user_id or not event.chat_id or not event.message_id or not event.sender_id:
            raise TrueConfError("unbound_ingress_delivery")
        key = IngressKey(self._origin, session.user_id, event.chat_id, event.message_id)
        used = False

        async def accept(persist: Callable[[IngressKey], Awaitable[IngressReceipt]]) -> IngressReceipt:
            nonlocal used
            if used:
                raise TrueConfError("ingress_delivery_already_attempted")
            if not self._ingress_session_current(session):
                raise TrueConfError("ingress_delivery_closed")
            used = True
            try:
                receipt = await persist(key)
            except Exception:  # noqa: BLE001 - adapter persistence may fail with private details
                raise TrueConfError("ingress_persistence_failed") from None
            if (
                type(receipt) is not IngressReceipt or receipt.key != key
                or receipt.status not in ("NEW", "DUPLICATE", "DISCARDED")
            ):
                raise TrueConfError("invalid_ingress_receipt")
            await self._ack_admitted(session, msg_id, receipt)
            return receipt

        return IngressDelivery(event, key, accept)

    async def _ack_admitted(self, session: _Session, msg_id: int, receipt: IngressReceipt) -> None:
        dispatch_started = False
        try:
            async with asyncio.timeout(self._timeout), session.send_lock:
                if not self._ingress_session_current(session):
                    raise IngressAckError(receipt, ambiguous=False)
                dispatch_started = True
                await self._wire_send(session, json.dumps({"type": 2, "id": msg_id}))
                session.unacknowledged_ingress.remove(msg_id)
        except asyncio.CancelledError:
            raise IngressAckCancelled(receipt) from None
        except (ConnectionClosed, OSError, TimeoutError):
            raise IngressAckError(receipt, ambiguous=dispatch_started) from None

    async def _reader(self, session: _Session) -> None:
        failure = None
        try:
            async for raw in session.websocket:
                if not isinstance(raw, str):
                    raise TrueConfError("invalid_websocket_frame")
                data = _parse_json(raw)
                if not isinstance(data, dict):
                    raise TrueConfError("invalid_wire_envelope")
                msg_id = _uint(data.get("id"), _MAX_ID)
                kind = _uint(data.get("type"))
                if msg_id is None or kind not in (1, 2):
                    raise TrueConfError("invalid_wire_envelope")
                if kind == 2:
                    future = session.pending.get(msg_id)
                    if future is not None and not future.done():
                        future.set_result(data.get("payload"))
                        if session.user_id is None:
                            await session.auth_done.wait()
                            if session.user_id is None:
                                return
                    continue
                if session.user_id is None:
                    raise TrueConfError("notification_before_auth")
                if session.local_close:
                    return
                method = data.get("method")
                payload = _object(data.get("payload"))
                message_type = _uint(payload.get("type"))
                if self._durable_ingress:
                    if _identifier(method) is None:
                        raise TrueConfError("invalid_notification_method")
                    if msg_id in session.unacknowledged_ingress:
                        raise TrueConfError("reused_pending_notification_id")
                    if method == "sendMessage":
                        if message_type is None:
                            raise TrueConfError("invalid_ingress_payload")
                        if message_type >= 200:
                            if len(session.unacknowledged_ingress) >= session.event_limit:
                                raise TrueConfError("event_queue_overflow")
                            session.unacknowledged_ingress.add(msg_id)
                            if message_type in (200, 202, 205):
                                session.queue.put_nowait(self._make_delivery(session, msg_id, _message(payload)))
                            # Other user envelopes stay unread. Only supported types reach the adapter.
                            continue
                if method == "sendMessage" and message_type in (200, 202, 205):
                    event = _message(payload)
                    if session.queue.qsize() >= session.event_limit:
                        raise TrueConfError("event_queue_overflow")
                    session.queue.put_nowait(event)
                async with session.send_lock:
                    await asyncio.wait_for(self._wire_send(session, json.dumps({"type": 2, "id": msg_id})), self._timeout)
        except TrueConfError as exc:
            failure = exc.reason
        except (ValueError, RecursionError):
            failure = "invalid_wire_json"
        except (ConnectionClosed, OSError, TimeoutError):
            failure = "websocket_disconnected"
        finally:
            session.ended = True
            for future in session.pending.values():
                if not future.done():
                    future.set_result(TrueConfError("websocket_disconnected", ambiguous=True))
            reason = None if session.local_close and failure in (None, "websocket_disconnected") else failure
            if reason is None and not session.local_close:
                reason = "websocket_disconnected"
            session.queue.put_nowait(reason)
            if not session.local_close:
                code = 1002 if failure not in (None, "websocket_disconnected") else 1000
                await session.websocket.close(code=code)

    def events(self) -> AsyncIterator[MessageEvent]:
        if self._durable_ingress:
            raise TrueConfError("use_ingress_deliveries")
        return cast(AsyncIterator[MessageEvent], self._items())

    def deliveries(self) -> AsyncIterator[IngressDelivery]:
        if not self._durable_ingress:
            raise TrueConfError("durable_ingress_disabled")
        return cast(AsyncIterator[IngressDelivery], self._items())

    async def _items(self) -> AsyncIterator[MessageEvent | IngressDelivery]:
        session = self._session
        if session is None:
            raise TrueConfError("not_connected")
        if session.consuming:
            raise TrueConfError("event_consumer_already_active")
        session.consuming = True
        try:
            while True:
                item = await session.queue.get()
                if isinstance(item, (MessageEvent, IngressDelivery)):
                    yield item
                    continue
                session.queue.put_nowait(item)
                if item is not None:
                    raise TrueConfError(item)
                return
        finally:
            session.consuming = False

    async def _request(self, session: _Session, method: str, payload: dict, *, before_dispatch=None) -> object:
        sent = False
        msg_id = None
        future = None

        async def exchange() -> object:
            nonlocal sent, msg_id, future
            async with session.send_lock:
                if session.ended or session.local_close:
                    raise TrueConfError("not_connected")
                if len(session.pending) >= 64 or session.next_id > _MAX_ID:
                    raise TrueConfError("request_capacity")
                msg_id = session.next_id
                session.next_id += 1
                try:
                    data = json.dumps(
                        {"type": 1, "id": msg_id, "method": method, "payload": payload},
                        ensure_ascii=True, separators=(",", ":"), allow_nan=False,
                    )
                except (ValueError, TypeError):
                    raise TrueConfError("invalid_request") from None
                if len(data) > _MAX_FRAME:
                    raise TrueConfError("request_too_large")
                if before_dispatch is not None:
                    before_dispatch()
                future = asyncio.get_running_loop().create_future()
                session.pending[msg_id] = future
                sent = True
                await self._wire_send(session, data)
            return await future

        try:
            async with asyncio.timeout(self._timeout):
                result = await exchange()
        except asyncio.TimeoutError:
            raise TrueConfError("request_timeout", ambiguous=sent) from None
        except asyncio.CancelledError:
            if sent:
                raise TrueConfRequestCancelled(method) from None
            raise
        except TrueConfError:
            raise
        except (ConnectionClosed, OSError):
            raise TrueConfError("websocket_request_failed", ambiguous=sent) from None
        finally:
            if msg_id is not None:
                session.pending.pop(msg_id, None)
            if future is not None and not future.done():
                future.cancel()
        if isinstance(result, TrueConfError):
            raise result
        if isinstance(result, dict) and "errorCode" in result:
            code = _uint(result["errorCode"], _MAX_ID)
            raise TrueConfError("server_error", ambiguous=code not in _REJECTION_CODES, error_code=code)
        return result

    async def _read(self, method: str, payload: dict) -> object:
        return await self._request(self._active(), method, payload)

    async def _file_rpc(self, session: _Session, method: str, payload: dict) -> dict:
        return _object(await self._request(session, method, payload))

    async def get_chat(self, chat_id: str) -> dict:
        chat_id = _require_id(chat_id, "invalid_chat_id")
        result = _object(await self._read("getChatByID", {"chatId": chat_id}))
        if result.get("chatId") != chat_id:
            raise TrueConfError("invalid_chat_response")
        return result

    async def list_chats(self, *, count: int = 10, page: int = 1) -> list[dict]:
        if type(count) is not int or not 1 <= count <= 50 or type(page) is not int or not 1 <= page <= _MAX_ID:
            raise TrueConfError("invalid_chat_page")
        result = await self._read("getChats", {"count": count, "page": page})
        if not isinstance(result, list) or len(result) > count or any(
            _identifier(_object(item).get("chatId")) is None for item in result
        ):
            raise TrueConfError("invalid_chats_response")
        return result

    async def get_message(self, message_id: str, *, chat_id: str | None = None) -> MessageEvent:
        message_id = _require_id(message_id, "invalid_message_id")
        if chat_id is not None:
            _require_id(chat_id, "invalid_chat_id")
        result = _message(await self._read("getMessageById", {"messageId": message_id}))
        if result.message_id != message_id or (chat_id is not None and result.chat_id != chat_id):
            raise TrueConfError("invalid_message_response")
        return result

    async def get_file_info(self, file_id: str) -> dict:
        file_id = _require_id(file_id, "invalid_file_id")
        result = _object(await self._read("getFileInfo", {"fileId": file_id}))
        if result.get("fileId") != file_id:
            raise TrueConfError("invalid_file_response")
        return result

    @staticmethod
    def _error_result(exc: TrueConfError) -> SendResult:
        return SendResult("UNKNOWN" if exc.ambiguous else "REJECTED", reason=exc.reason, error_code=exc.error_code)

    async def _send_message(self, session: _Session, method: str, payload: dict, *, before_dispatch=None) -> SendResult:
        try:
            ack = _object(await self._request(session, method, payload, before_dispatch=before_dispatch))
            message_id = _identifier(ack.get("messageId"))
            file_id = _identifier(ack.get("fileId"))
            timestamp = _uint(ack.get("timestamp"))
            if (
                ack.get("chatId") != payload["chatId"] or message_id is None or timestamp is None
                or (method == "sendFile" and file_id is None)
            ):
                return SendResult("UNKNOWN", reason="invalid_send_ack")
            return SendResult("ACK", message_id=message_id, file_id=file_id, timestamp=timestamp)
        except TrueConfError as exc:
            return self._error_result(exc)

    async def send_text(self, chat_id: str, text: str, reply_to: str | None = None,
                        *, parse_mode: str = "text") -> SendResult:
        try:
            chat_id = _require_id(chat_id, "invalid_chat_id")
            if not isinstance(text, str) or not text or len(text) > _MAX_FRAME:
                raise TrueConfError("invalid_text")
            if parse_mode not in {"text", "markdown"}:
                raise TrueConfError("invalid_parse_mode")
            payload: dict[str, Any] = {"chatId": chat_id, "content": {"text": text, "parseMode": parse_mode}}
            if reply_to is not None:
                payload["replyMessageId"] = _require_id(reply_to, "invalid_reply_id")
            return await self._send_message(self._active(), "sendMessage", payload)
        except TrueConfError as exc:
            return self._error_result(exc)

    async def send_file(self, chat_id: str, path: str | os.PathLike[str], reply_to: str | None = None,
                        *, caption: str | None = None, before_dispatch=None) -> SendResult:
        try:
            chat_id = _require_id(chat_id, "invalid_chat_id")
            if reply_to is not None:
                raise TrueConfError("unsupported_file_reply")
            if caption is not None and (not isinstance(caption, str) or len(caption) > _MAX_FRAME):
                raise TrueConfError("invalid_file_caption")
            session = self._active()
            staged_id = await upload_file(
                self._http_client(), self._origin, lambda method, payload: self._file_rpc(session, method, payload),
                path, max_bytes=self._max_upload_bytes, before_post=before_dispatch,
            )
        except FileTransferError as exc:
            reason = "staging_outcome_unknown" if exc.ambiguous else exc.reason
            return SendResult("REJECTED", reason=reason)
        except TrueConfError as exc:
            return SendResult("REJECTED", reason=exc.reason, error_code=exc.error_code)
        content: dict[str, Any] = {"temporalFileId": staged_id}
        if caption:
            content["caption"] = {"text": caption, "parseMode": "text"}
        return await self._send_message(session, "sendFile", {"chatId": chat_id, "content": content},
                                        before_dispatch=before_dispatch)

    async def download_file(
        self, file_id: str, target: str | os.PathLike[str], *,
        max_bytes: int = DEFAULT_FILE_BYTES, expected_size: int | None = None,
    ) -> Path:
        session = self._active()
        try:
            return await download_file(
                self._http_client(), self._origin, lambda method, payload: self._file_rpc(session, method, payload),
                file_id, target, max_bytes=max_bytes, expected_size=expected_size,
            )
        except FileTransferError as exc:
            raise TrueConfError(exc.reason, ambiguous=exc.ambiguous) from None
