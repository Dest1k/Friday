"""Join native call correlation to a durable post-authorization ingress receipt.

This authorizes no worker by itself: verified workspace/input bytes, budgets,
native supervision and adapter readiness are separate controller prerequisites.
"""
from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
import copy
import hashlib
import json
from pathlib import Path
import re

from .associations import Associations, _sync_directory
from .boundary import bound_owner, parse_brief, work_handler

KEY = "admitted_ingress.v1"
_PAYLOAD_KEY = "admitted_ingress_payload.v1"
CALL_FIELDS = ("task_id", "session_id", "turn_id", "api_request_id", "tool_call_id")
_call = ContextVar("friday_native_call", default=None)


def _text(value, limit=512, empty=False):
    if not isinstance(value, str) or (not empty and not value.strip()) or "\x00" in value:
        raise ValueError("invalid_ingress")
    if len(value.encode("utf-8")) > limit:
        raise ValueError("invalid_ingress")
    return value


def _encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")


def _snapshot(value):
    if isinstance(value, dict) and value.get('platform') == 'cli':
        from hermes_cli.friday_cli_work import validate_ingress
        return validate_ingress(value)
    top = {"platform", "session_key", "source_profile", "transport_profile", "runtime_profile", "message"}
    fields = {"bot_id", "user_id", "chat_id", "thread_id", "message_id", "platform_update_id", "reply_to_message_id", "media"}
    if (not isinstance(value, dict) or set(value) not in (top, top | {"chat_type"})
            or value["platform"] != "telegram"):
        raise ValueError("unproved_ingress")
    if "chat_type" in value and (not isinstance(value["chat_type"], str)
                                or value["chat_type"] not in {"dm", "group", "channel", "thread"}):
        raise ValueError("invalid_ingress_chat_type")
    for key in top - {"message"}:
        _text(value[key], empty=key == "source_profile")
    message = value["message"]
    if not isinstance(message, dict) or set(message) != fields:
        raise ValueError("invalid_ingress")
    for key in fields - {"media"}:
        _text(message[key], empty=key in {"thread_id", "reply_to_message_id"})
    if not isinstance(message["media"], list) or len(message["media"]) > 64:
        raise ValueError("invalid_ingress")
    for media in message["media"]:
        required_media = {"local_reference", "mime_type", "origin"}
        if not isinstance(media, dict) or set(media) not in (required_media, required_media | {"content"}):
            raise ValueError("invalid_ingress")
        _text(media["local_reference"], 2048)
        _text(media["mime_type"], 256)
        if "content" in media:
            content = media["content"]
            if (not isinstance(content, dict) or set(content) != {"size_bytes", "sha256"}
                    or type(content["size_bytes"]) is not int or content["size_bytes"] < 0
                    or not isinstance(content["sha256"], str)
                    or not re.fullmatch(r"[0-9a-f]{64}", content["sha256"])):
                raise ValueError("invalid_ingress_content")
        origin = media["origin"]
        if origin is not None:
            required = {"bot_id", "chat_id", "thread_id", "message_id", "file_id", "file_unique_id", "declared_bytes"}
            if not isinstance(origin, dict) or set(origin) != required:
                raise ValueError("invalid_ingress")
            for key in required - {"declared_bytes"}:
                _text(origin[key], empty=key == "thread_id")
            size = origin["declared_bytes"]
            if size is not None and (type(size) is not int or size < 0):
                raise ValueError("invalid_ingress")
            if any(origin[k] != message[k] for k in ("bot_id", "chat_id", "thread_id")):
                raise ValueError("foreign_input_origin")
    if len(_encoded(value)) > 65536:
        raise ValueError("ingress_too_large")
    return copy.deepcopy(value)


def _receipt_key(value):
    # One routed message cannot silently acquire another bot/update identity.
    if value.get('platform') == 'cli':
        return hashlib.sha256(_encoded(['cli', value['session_id'], value['runtime_home'],
                                      value['input']['native_message_id']])).hexdigest()
    return hashlib.sha256(_encoded([
        value["session_key"], value["source_profile"], value["message"]["message_id"]
    ])).hexdigest()


def delivery_route(matched_ingress):
    """Route from the persisted, matched receipt, never an ambient session.

    Historical receipts remain readable, but cannot invent the missing native
    chat type. The gateway rechecks current authorization and actual adapter.
    """
    value = _snapshot(matched_ingress)
    if value['platform'] == 'cli':
        return copy.deepcopy(value['route'])
    if "chat_type" not in value:
        raise ValueError("missing_admitted_delivery_route")
    message = value["message"]
    return {
        "source": {
            "platform": value["platform"], "chat_id": message["chat_id"],
            "chat_type": value["chat_type"], "user_id": message["user_id"],
            "thread_id": message["thread_id"] or None, "message_id": message["message_id"],
        },
        "transport_profile": value["transport_profile"],
        "runtime_profile": value["runtime_profile"], "bot_id": message["bot_id"],
    }


def native_call_scope(*, tool_name, args, next_call, **context):
    """Transport correlation through the supported middleware, never effects.

    Native policy is inside next_call. If this wrapper fails, Hermes may fall
    through; therefore the registered handler independently requires a scope.
    """
    if tool_name not in {"friday_work", "friday_result"}:
        return next_call(args)
    # Mask an outer invocation before allocation/validation can fail. Hermes
    # falls through after middleware exceptions, so no such fallback may use
    # the parent's correlation as proof for this call.
    outer = _call.get()
    token = _call.set(None)
    try:
        try:
            if outer is not None:
                raise ValueError('nested_native_call')
            from hermes_cli.friday_cli_work import is_cli, admitted_call
            if is_cli():
                _, verified = admitted_call(context)
                identity = tuple(verified[key] for key in CALL_FIELDS)
            else:
                identity = tuple(_text(context.get(key)) for key in CALL_FIELDS)
        except Exception:
            identity = None
        _call.set(identity)
        # Native middleware propagates downstream errors without replay. Keep
        # the surrounding call usable when it handles an inner tool failure.
        return next_call(args)
    finally:
        _call.reset(token)


def _receipt_document(document):
    if (not isinstance(document, dict) or set(document) != {"schema_version", "receipts"}
            or type(document["schema_version"]) is not int or document["schema_version"] != 1
            or not isinstance(document["receipts"], dict)):
        raise ValueError("invalid_ingress_store")
    for key, value in document["receipts"].items():
        if key != _receipt_key(_snapshot(value)):
            raise ValueError("invalid_ingress_store")
    return document


def _payload_value(snapshot, payload):
    if (type(payload) is not dict or set(payload) != {"kind", "sha256", "date"}
            or payload["kind"] not in ("caption", "text")
            or not isinstance(payload["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", payload["sha256"]) is None
            or type(payload["date"]) is not int or not 0 < payload["date"] < 2**63
            or snapshot["platform"] != "telegram" or snapshot.get("chat_type") != "dm"):
        raise ValueError("invalid_ingress_payload")
    message = snapshot["message"]
    if message["chat_id"] != message["user_id"] or message["thread_id"]:
        raise ValueError("foreign_ingress_payload")
    media = message["media"]
    if payload["kind"] == "text":
        if media:
            raise ValueError("invalid_ingress_payload_media")
    else:
        if len(media) != 1:
            raise ValueError("invalid_ingress_payload_media")
        origin, content = media[0]["origin"], media[0].get("content")
        if (origin is None or content is None or origin["message_id"] != message["message_id"]
                or type(origin["declared_bytes"]) is not int
                or not 0 < content["size_bytes"] == origin["declared_bytes"]):
            raise ValueError("foreign_ingress_payload_document")
    return dict(payload)


def _payload_map(value, receipts):
    if type(value) is not dict or any(key not in receipts for key in value):
        raise ValueError("invalid_ingress_payload_store")
    for key, payload in value.items():
        _payload_value(receipts[key], payload)
    return value


def _record_snapshot(admitted_ingress, session_key, message_id, source, platform):
    snapshot = _snapshot(admitted_ingress)
    message = snapshot["message"]
    if (platform != snapshot["platform"] or session_key != snapshot["session_key"]
            or message_id != message["message_id"] or not isinstance(source, dict)
            or any((source.get(k) or "") != message[k] for k in ("user_id", "chat_id", "thread_id", "message_id"))
            or (source.get("profile") or "") != snapshot["source_profile"]):
        raise ValueError("ingress_source_mismatch")
    chat_type = source.get("chat_type")
    if (not isinstance(chat_type, str) or chat_type not in {"dm", "group", "channel", "thread"}
            or ("chat_type" in snapshot and snapshot["chat_type"] != chat_type)):
        raise ValueError("ingress_source_mismatch")
    snapshot["chat_type"] = chat_type
    return snapshot


_PAIR_COMMIT_SEAL = object()


@dataclass(frozen=True, eq=False)
class _IngressPairCommit:
    receipt_key: str
    update_id: str
    pair_sha256: str
    durable: object
    _seal: object


def _pair_sha256(snapshot, payload):
    return hashlib.sha256(_encoded([snapshot, payload])).hexdigest()


class IngressAdmissions:
    def __init__(self, state):
        self.state = state
        self.associations = Associations(state)

    def _read(self):
        return _receipt_document(self.associations.state_get(KEY, {"schema_version": 1, "receipts": {}}))

    def record(self, *, admitted_ingress=None, session_key, message_id, source, platform,
               telegram_payload_v1=None, **_):
        snapshot = _record_snapshot(admitted_ingress, session_key, message_id, source, platform)
        if telegram_payload_v1 is not None:
            return self._record_with_payload(snapshot, _payload_value(snapshot, telegram_payload_v1))
        with self.associations._locked():
            document = self._read()
            key = _receipt_key(snapshot)
            prior = document["receipts"].get(key)
            if prior is not None:
                if prior != snapshot:
                    raise ValueError("ingress_identity_conflict")
                return
            document["receipts"][key] = snapshot
            self.associations.state_set(KEY, document)
            _sync_directory(Path(self.state.data_dir))

    def record_payload_commit(self, *, admitted_ingress, session_key, message_id, source, platform,
                              telegram_payload_v1):
        """Return a new pair's native close evidence after the original writer settles."""
        snapshot = _record_snapshot(admitted_ingress, session_key, message_id, source, platform)
        payload = _payload_value(snapshot, telegram_payload_v1)
        return self._record_with_payload(snapshot, payload, return_commit=True)

    def _payload_state(self):
        from hermes_cli.friday_admin_control import _CURRENT as admin_scope
        from hermes_cli.friday_cli_work import is_cli

        association = self.associations
        if (association.state is not self.state or association._operator is not None
                or association._cli_authority is not None or is_cli()
                or admin_scope.get() is not None):
            raise PermissionError("invalid_ingress_payload_storage_scope")
        association._check_local_state()
        return association.state

    def _record_with_payload(self, snapshot, payload, *, return_commit=False):
        from hermes_cli.friday_native_state import RetainedStateTransaction

        key = _receipt_key(snapshot)
        state = self._payload_state()
        with self.associations._locked():
            if self._payload_state() is not state:
                raise PermissionError("invalid_ingress_payload_storage_scope")
            with RetainedStateTransaction(state, cutoff=None, lock_deadline=None,
                                          lock_budget=self.associations._lock_allowance.get()) as transaction:
                document = _receipt_document(transaction.data.get(KEY, {"schema_version": 1, "receipts": {}}))
                receipts = document["receipts"]
                payloads = _payload_map(transaction.data.get(_PAYLOAD_KEY, {}), receipts)
                if key not in receipts:
                    updated = {"schema_version": 1, "receipts": {**receipts, key: snapshot}}
                    transaction.replace(KEY, updated, ingress_payloads={**payloads, key: payload})
                elif receipts[key] == snapshot and (key not in payloads or payloads[key] == payload):
                    # Preserve a legacy receipt and avoid writing on replay.
                    return
                else:
                    updated = None
            if self._payload_state() is not state:
                raise PermissionError("invalid_ingress_payload_storage_scope")
            if updated is None:
                raise ValueError("ingress_identity_conflict")
        if return_commit:
            return _IngressPairCommit(key, snapshot["message"]["platform_update_id"],
                                      _pair_sha256(snapshot, payload), transaction.witness(),
                                      _PAIR_COMMIT_SEAL)

    def observe_payload_pair(self, *, admitted_ingress, session_key, message_id, source, platform,
                             telegram_payload_v1, lock_deadline=None):
        """Compare one stored pair without claiming a durable commit or retrying it."""
        snapshot = _record_snapshot(admitted_ingress, session_key, message_id, source, platform)
        payload = _payload_value(snapshot, telegram_payload_v1)
        key = _receipt_key(snapshot)
        state = self._payload_state()
        data, identity = state._read_storage_readonly(lock_deadline=lock_deadline, with_identity=True)
        if self._payload_state() is not state:
            raise PermissionError("invalid_ingress_payload_storage_scope")
        receipts = _receipt_document(data.get(KEY, {"schema_version": 1, "receipts": {}}))["receipts"]
        payloads = _payload_map(data.get(_PAYLOAD_KEY, {}), receipts)
        if key not in receipts:
            status = "ABSENT"
        elif receipts[key] != snapshot or (key in payloads and payloads[key] != payload):
            status = "CONFLICT"
        else:
            status = "PRESENT" if key in payloads else "RECEIPT_ONLY"
        return {"pair": status, "state": identity}

    def match(self, owner, *, task_id, session_id):
        call = _call.get()
        original_session = owner['session_id'] if owner.get('platform') == 'cli' else owner['id']
        if call is None or call[:2] != (task_id, session_id) or session_id != original_session:
            raise ValueError("missing_native_correlation")
        if owner.get('platform') == 'cli':
            from hermes_cli.friday_cli_work import admitted_call, check_owner
            snapshot, native = admitted_call(dict(zip(CALL_FIELDS, call)))
            check_owner(owner, snapshot)
            with self.associations._locked():
                document = self._read()
                key = _receipt_key(snapshot)
                prior = document['receipts'].get(key)
                if prior is not None and prior != snapshot:
                    raise ValueError('ingress_identity_conflict')
                if prior is None:
                    document['receipts'][key] = snapshot
                    self.associations.state_set(KEY, document)
                _sync_directory(Path(self.state.data_dir))
            check_owner(owner, snapshot)
            return copy.deepcopy(snapshot), native
        lookup = {"session_key": owner["key"], "source_profile": owner["profile"],
                  "message": {"message_id": owner["message_id"]}}
        with self.associations._locked():
            snapshot = self._read()["receipts"].get(_receipt_key(lookup))
            if snapshot is None:
                raise ValueError("missing_admitted_ingress")
            if (snapshot["platform"] != owner["platform"]
                    or ("chat_type" in snapshot and snapshot["chat_type"] != owner.get("chat_type"))
                    or any(snapshot["message"][k] != owner[k] for k in ("user_id", "chat_id", "thread_id", "message_id"))):
                raise ValueError("foreign_admitted_ingress")
            # Native state may have committed before an earlier caller failed
            # its directory barrier. Complete that barrier before using it.
            _sync_directory(Path(self.state.data_dir))
            return copy.deepcopy(snapshot), dict(zip(CALL_FIELDS, call))

    def handle(self, args, **kwargs):
        try:
            parse_brief(args)
            owner = bound_owner(session_id=kwargs.get("session_id"))
            self.match(owner, task_id=kwargs.get("task_id"), session_id=kwargs.get("session_id"))
        except (ValueError, UnicodeError, RuntimeError, OSError):
            return json.dumps({"accepted": False, "error": "unproved_admission"})
        # This candidate proves the join; the controller/worker readiness gate
        # stays closed until actual native supervision and adapters are wired.
        return work_handler(args, **kwargs)
