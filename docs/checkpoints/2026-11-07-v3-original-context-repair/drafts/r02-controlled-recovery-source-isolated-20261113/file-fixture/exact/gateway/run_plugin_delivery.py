"""Strict original-route, immutable-document delivery for the public plugin context."""
from __future__ import annotations

import asyncio
import hashlib
import math
from collections.abc import Mapping

from gateway.config import Platform
from gateway.session import SessionSource
from gateway.session_identity import canonical_identity, restore_identity


def freeze_route(route):
    """Copy only the minimal persisted native source; reject all ambiguous defaults."""
    if not isinstance(route, Mapping) or not isinstance(route.get("source"), Mapping):
        raise ValueError("original_route_required")
    fields = ("platform", "chat_id", "chat_type", "user_id", "thread_id", "message_id")
    try:
        source = {key: route["source"][key] for key in fields}
        result = {key: route[key] for key in ("transport_profile", "runtime_profile", "bot_id")}
    except KeyError:
        raise ValueError("incomplete_original_route") from None
    for value in [*result.values(), *(source[key] for key in fields if key != "thread_id")]:
        if not isinstance(value, str) or not value or value != value.strip():
            raise ValueError("invalid_original_route")
    if source["platform"] != "telegram" or source["chat_type"] not in {"dm", "group", "channel", "thread"}:
        raise ValueError("unsupported_original_route")
    for value in (result["bot_id"], source["user_id"], source["message_id"]):
        if not value.isascii() or not value.isdecimal() or int(value) <= 0:
            raise ValueError("invalid_original_identity")
    if str(int(source["chat_id"])) != source["chat_id"] or int(source["chat_id"]) == 0:
        raise ValueError("invalid_original_chat")
    topic = source["thread_id"]
    if topic is not None and (not isinstance(topic, str) or not topic.isascii()
                              or not topic.isdecimal() or int(topic) <= 0):
        raise ValueError("invalid_original_topic")
    source["profile"] = result["runtime_profile"]
    result["source"] = source
    return result


def resolve_document_route(runner, context, route):
    """Restore original transport identity, never consult a mutable latest session."""
    from hermes_constants import hermes_home_key
    route = freeze_route(route)
    profile = runner._served_profile_for_home(context._manager.home_path)
    if profile is None or profile != route["runtime_profile"]:
        raise RuntimeError("plugin_profile_not_served")
    source = SessionSource.from_dict(route["source"])
    identity = restore_identity(source, runner=runner, transport_profile=route["transport_profile"])
    if identity is None:
        # Standalone mode still requires explicit transport ownership and profile scope.
        if route["transport_profile"] != profile:
            raise RuntimeError("transport_profile_mismatch")
        adapter = runner._adapters_for_profile(profile).get(Platform.TELEGRAM)
        if adapter is None:
            raise RuntimeError("original_bot_offline")
        identity = canonical_identity(source, runner=runner, adapter=adapter,
                                      transport_profile=route["transport_profile"])
    if (identity is None or identity.transport_inferred
            or identity.runtime_profile != profile
            or hermes_home_key(identity.runtime_home) != hermes_home_key(context._manager.home_path)):
        raise RuntimeError("runtime_home_mismatch")
    adapter = runner._delivery_adapter_for(source)
    if (adapter is None or adapter.is_connected is not True
            or str(getattr(getattr(adapter, "_bot", None), "id", "")) != route["bot_id"]):
        raise RuntimeError("original_bot_offline")
    registered, owner = runner._owning_profile(adapter, source.platform)
    actual_owner = owner or getattr(runner, "_primary_profile_name", None)
    if not registered or actual_owner != route["transport_profile"]:
        raise RuntimeError("transport_owner_mismatch")
    if not runner._is_user_authorized_for_source(source, allow_adapter_delegation=False):
        raise RuntimeError("original_route_no_longer_authorized")
    return source, adapter


async def deliver_document(runner, context, *, route, data, file_name, caption, timeout, authority_check=None):
    if (type(data) is not bytes or not isinstance(file_name, str) or not file_name
            or len(file_name) > 255 or any(ord(c) < 32 or c in "/\\" for c in file_name)
            or file_name in {".", ".."} or (caption is not None and not isinstance(caption, str))
            or isinstance(timeout, bool) or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout) or timeout <= 0):
        return {"state": "FAILED", "error": "invalid_document"}
    try:
        route = freeze_route(route)
        source, adapter = resolve_document_route(runner, context, route)
    except Exception:  # health: allow BLE001 -- This route refusal precedes every send; safe to retry only after configuration repair.
        return {"state": "FAILED", "error": "gateway_document_route_rejected"}
    if not callable(getattr(adapter, "send_document_bytes", None)):
        return {"state": "FAILED", "error": "document_bytes_unsupported"}
    from gateway.platforms.base import SendResult, _thread_metadata_for_source
    expected = {
        "kind": "document", "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data), "file_name": file_name, "bot_id": route["bot_id"],
        "chat_id": source.chat_id, "thread_id": source.thread_id, "reply_to": source.message_id,
    }
    def check():
        if authority_check is not None:
            authority_check()
        if resolve_document_route(runner, context, route)[1] is not adapter:
            raise ValueError('original_adapter_replaced')
    metadata = _thread_metadata_for_source(source, source.message_id) or {}
    metadata['_friday_document_authority'] = (check, freeze_route(route))
    try:
        check()
        result = await asyncio.wait_for(adapter.send_document_bytes(
            source.chat_id, data, file_name=file_name, caption=caption, reply_to=source.message_id,
            metadata=metadata), timeout)
    except Exception:  # health: allow BLE001 -- Transport failures may have committed; never expose SDK error text or traceback.
        return {"state": "UNKNOWN", "error": "document_ack_unavailable", **expected}
    proof = result.raw_response if isinstance(result, SendResult) else None
    if (isinstance(result, SendResult) and result.success is True and isinstance(proof, dict)
            and all(proof.get(key) == value for key, value in expected.items())
            and isinstance(result.message_id, str) and result.message_id.isdecimal()
            and int(result.message_id) > 0 and proof.get("message_id") == result.message_id):
        return {"state": "DELIVERED", **expected, "message_id": result.message_id}
    return {"state": "UNKNOWN", "error": "document_ack_unavailable", **expected}


_ORDINARY_DOCUMENTS = 'ordinary_documents.v1'


def _ordinary_marker(selection):
    from hermes_cli.friday_native_state import encoded
    return encoded({'schema': 'friday.ordinary-document-attempt.v1', 'selection': selection})


def _ordinary_commit(state, value, previous, *, journals):
    from hermes_cli.friday_native_state import observe_commit_return, require_commit_return
    witness = state.set_commit(_ORDINARY_DOCUMENTS, value, expected_value=previous,
                               compare=True, journals=journals)
    require_commit_return(state, observe_commit_return(state, witness))


def _ordinary_prior_attempt(state, cap, selection, relative, route):
    """Read existing bounded immutable history under its native custody lock.

    The last mutable row alone cannot detect A -> B -> replay A. Legacy row
    and receipt journals remain authoritative when no ingress marker exists.
    """
    import json
    import os
    import copy
    from hermes_cli.friday_native_state import (
        RetainedStateTransaction, MAX_JOURNAL, _private, identity,
    )
    route = freeze_route(route)
    with RetainedStateTransaction(state, cutoff=None, lock_deadline=None, lock_budget=None) as tx:
        names, _ = tx.storage_inventory()
        for name in names:
            cap.check()
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=tx.dirfd)
            try:
                before = os.fstat(fd); _private(before, 0o400)
                body = tx.read_exact(fd, MAX_JOURNAL)
                after = os.fstat(fd)
                named = os.stat(name, dir_fd=tx.dirfd, follow_symlinks=False)
                _private(after, 0o400); _private(named, 0o400)
                if (identity(before) != identity(after) or identity(before) != identity(named)
                        or before.st_size != len(body) or after.st_size != len(body)
                        or name != name.rsplit('-', 1)[0] + '-' + hashlib.sha256(body).hexdigest() + '.json'):
                    raise ValueError('ordinary_document_history_invalid')
                row = json.loads(body)
            finally:
                os.close(fd)
            if not isinstance(row, dict):
                continue
            if row.get('schema') == 'friday.ordinary-document-attempt.v1' and row.get('selection') == selection:
                if 'route' in row and freeze_route(row['route']) == route:
                    raise ValueError('delivery_requires_reconciliation')
            if row.get('relative_path') == relative and 'route' in row:
                if freeze_route(row['route']) == route:
                    raise ValueError('delivery_requires_reconciliation')
            if row.get('selection') == selection and 'receipt' in row:
                receipt = row['receipt']
                if (not isinstance(receipt, dict) or receipt.get('kind') != 'document'
                        or any(key not in receipt for key in ('reply_to', 'bot_id', 'chat_id', 'thread_id'))):
                    raise ValueError('ordinary_document_history_invalid')
                if (receipt['reply_to'] == route['source']['message_id']
                        and receipt['bot_id'] == route['bot_id']
                        and receipt['chat_id'] == route['source']['chat_id']
                        and receipt['thread_id'] == route['source']['thread_id']):
                    raise ValueError('delivery_requires_reconciliation')
        cap.check()
        return copy.deepcopy(tx.data.get(_ORDINARY_DOCUMENTS))


def _begin_ordinary_document(cap, relative, data, route, file_name):
    """Use existing native durable CAS + immutable UNKNOWN before a send effect.

    Only a confirmed delivery permits a later original request on the same
    owned route. That request may select a revised immutable snapshot at the
    same workspace path. Unknown attempts and the same ingress stay fenced;
    native immutable journals retain earlier acknowledgements.
    """
    import copy
    from hermes_cli.plugins_state import PluginState
    from hermes_cli.friday_native_state import encoded
    state = PluginState('friday_rework')
    selection = hashlib.sha256(encoded([cap.key, relative])).hexdigest()
    route = freeze_route(route)
    previous = _ordinary_prior_attempt(state, cap, selection, relative, route)
    marker = _ordinary_marker(selection)
    ingress_marker = encoded({'schema': 'friday.ordinary-document-attempt.v1',
                              'selection': selection, 'route': route})
    marker_name = 'friday-unknown-' + hashlib.sha256(marker).hexdigest() + '.json'
    if previous is not None and (not isinstance(previous, dict)
            or previous.get('schema') != _ORDINARY_DOCUMENTS or not isinstance(previous.get('files'), dict)):
        raise ValueError('ordinary_document_journal_invalid')
    value = copy.deepcopy(previous) if previous is not None else {'schema': _ORDINARY_DOCUMENTS, 'files': {}}
    # A lost/missing current state cannot erase its immutable uncertain history.
    old = value['files'].get(selection)
    if old is None and (state.data_dir / marker_name).exists():
        raise ValueError('delivery_requires_reconciliation')
    if old is not None:
        if old.get('state') != 'DELIVERED':
            raise ValueError('delivery_requires_reconciliation')
        before, after = freeze_route(old['route']), freeze_route(route)
        if (before['source']['message_id'] == after['source']['message_id']
                or {k:v for k,v in before.items() if k != 'source'} != {k:v for k,v in after.items() if k != 'source'}
                or {k:v for k,v in before['source'].items() if k != 'message_id'} !=
                   {k:v for k,v in after['source'].items() if k != 'message_id'}):
            raise ValueError('delivery_requires_reconciliation')
    if len(value['files']) >= 10000:
        raise ValueError('ordinary_document_journal_full')
    row = {'state': 'UNKNOWN', 'relative_path': relative, 'sha256': hashlib.sha256(data).hexdigest(),
           'bytes': len(data), 'file_name': file_name, 'route': freeze_route(route), 'receipt': None}
    value['files'][selection] = row
    cap.check()
    _ordinary_commit(state, value, previous,
                     journals=(('unknown', marker), ('unknown', ingress_marker), ('unknown', encoded(row))))
    return state, selection, value


def _ordinary_authority(adapter, source):
    """Retain the admitted ingress and recheck its live authority at the SDK boundary."""
    from types import SimpleNamespace
    from hermes_cli.friday_user_scope import current, ordinary_file_source
    from gateway.session_identity import identity_of
    cap = current(required=True)
    route = freeze_route(getattr(source, '_friday_document_route', None))
    runner = getattr(adapter, 'gateway_runner', None)
    context = SimpleNamespace(_manager=SimpleNamespace(home_path=cap.home))
    def check():
        cap.check()
        identity = identity_of(source)
        if (current(required=True) is not cap or ordinary_file_source() is not source
                or source.platform != Platform.TELEGRAM or identity is None or identity.transport_inferred
                or identity.runtime_home != cap.home or identity.runtime_profile != cap.profile
                or identity.transport_profile != cap.principal[1] or source.user_id != cap.principal[3]
                or runner is None or getattr(adapter, 'gateway_runner', None) is not runner
                or str(getattr(getattr(adapter, '_bot', None), 'id', '')) != cap.principal[2]):
            raise ValueError('original_source_required')
        actual = freeze_route({'transport_profile': identity.transport_profile,
            'runtime_profile': cap.profile, 'bot_id': cap.principal[2],
            'source': {'platform': source.platform.value, **{key: getattr(source, key) for key in
                ('chat_id', 'chat_type', 'user_id', 'thread_id', 'message_id')}}})
        if actual != route or freeze_route(getattr(source, '_friday_document_route', None)) != route:
            raise ValueError('native_original_route_required')
        if resolve_document_route(runner, context, route)[1] is not adapter:
            raise ValueError('original_adapter_replaced')
    check()
    return cap, runner, context, freeze_route(route), check


async def deliver_ordinary_document(adapter, source, path, *, caption=None, file_name=None):
    """Managed ordinary MEDIA uses the plugin's exact original-route byte send.

    No worker, synthetic task or product activation is introduced. The native
    source capability authorizes the own workspace, bot and original reply.
    """
    from pathlib import Path
    from hermes_cli.friday_user_scope import workspace_document
    from gateway.platforms.base import SendResult
    try:
        cap, runner, context, route, check = _ordinary_authority(adapter, source)
        if caption is not None:
            from hermes_cli.friday_user_scope import guard_gateway_reply
            guarded, blocked = guard_gateway_reply(source, caption)
            if blocked or guarded != caption or not _ordinary_caption_fits(caption):
                return SendResult(success=False, error='gateway_document_caption_rejected')
        data, relative = workspace_document(path)
        from gateway.run_attachment_presentation import original_document_name
        name = file_name or original_document_name(source, cap, relative, data) or Path(relative).name
        if (not isinstance(name, str) or not name or len(name) > 255
                or name in {'.', '..'} or any(ord(c) < 32 or c in '/\\' for c in name)):
            raise ValueError('invalid_document_name')
        session_id = getattr(source, '_friday_document_session_id', None)
        if not isinstance(session_id, str) or not session_id:
            raise ValueError('original_session_required')
        state, selection, reserved = _begin_ordinary_document(cap, relative, data, route, name)
    except Exception:
        return SendResult(success=False, error='gateway_document_preflight_rejected')
    # Cancellation or ANY commit/ack uncertainty leaves the original UNKNOWN.
    try:
        cap.check()
        await _ordinary_transcript(runner, session_id, relative, 'UNKNOWN', hashlib.sha256(data).hexdigest())
        receipt = await deliver_document(runner, context, route=route, data=data,
                                         file_name=name, caption=caption, timeout=30, authority_check=check)
        cap.check()
        if receipt.get('state') != 'DELIVERED':
            return SendResult(success=False, error='document_delivery_UNKNOWN')
        import copy
        from hermes_cli.friday_native_state import encoded
        candidate = copy.deepcopy(reserved)
        candidate['files'][selection].update(state='DELIVERED', receipt=receipt)
        _ordinary_commit(state, candidate, reserved,
                         journals=(('candidate', encoded({'selection': selection, 'receipt': receipt})),))
        await _ordinary_transcript(runner, session_id, relative, 'DELIVERED', receipt['sha256'])
        return SendResult(success=True, message_id=receipt['message_id'], raw_response=receipt)
    except Exception:
        return SendResult(success=False, error='document_delivery_UNKNOWN')


def _ordinary_caption_fits(caption):
    """Keep the complete plain-text answer within the native Telegram caption budget."""
    if not isinstance(caption, str) or not caption:
        return False
    try:
        return len(caption.encode('utf-16-le')) // 2 <= 1024
    except UnicodeEncodeError:
        return False


async def deliver_ordinary_files(adapter, source, paths, *, record_delivery=None, caption=None):
    """Shared managed final-MEDIA dispatcher for streaming and ordinary replies.

    Unmanaged native profiles continue through their original media branches.
    All managed local media keeps immutable bytes by using native documents.
    """
    from hermes_cli.friday_user_scope import ordinary_file_source
    admitted = getattr(source, '_friday_user_scope', None)
    if admitted is None:
        # Detect an active managed scope whose source was swapped/cleared.
        if ordinary_file_source() is not None:
            from gateway.platforms.base import SendResult
            if record_delivery: record_delivery(SendResult(success=False, error='gateway_document_route_rejected'))
            return True
        return False
    paths = list(dict.fromkeys(paths))
    if caption is not None and (len(paths) != 1 or not _ordinary_caption_fits(caption)):
        # No effect occurred: the caller may use its usual full-text + files path.
        return False
    for path in paths:
        result = await deliver_ordinary_document(adapter, source, path, caption=caption)
        if record_delivery is not None: record_delivery(result)
        if not result.success and result.error != 'gateway_document_caption_rejected':
            # A requested file's outcome is an ordinary reply, independently of
            # optional diagnostic suppression. Its own uncertain effect is fenced.
            await _ordinary_document_outcome(adapter, source, path, record_delivery)
    return True


async def _ordinary_document_outcome(adapter, source, path, record_delivery):
    import copy
    import os
    from hermes_cli.plugins_state import PluginState
    from hermes_cli.friday_native_state import encoded
    from gateway.platforms.base import SendResult, _thread_metadata_for_source
    try:
        cap, runner, _, route, check = _ordinary_authority(adapter, source)
        session_id = getattr(source, '_friday_document_session_id', None)
        if not isinstance(session_id, str) or not session_id:
            return
        path_key = os.path.normpath(os.path.join(str(cap.home / 'workspace'), os.fspath(path)))
        outcome_id = hashlib.sha256(encoded([cap.key, path_key, route])).hexdigest()
        marker = encoded({'schema': 'friday.ordinary-document-outcome.v1',
                          'outcome_id': outcome_id, 'route': route, 'state': 'PENDING'})
        state = PluginState('friday_rework')
        previous = state.get(_ORDINARY_DOCUMENTS)
        if previous is not None and (not isinstance(previous, dict)
                or previous.get('schema') != _ORDINARY_DOCUMENTS or not isinstance(previous.get('files'), dict)):
            return
        value = copy.deepcopy(previous) if previous is not None else {'schema': _ORDINARY_DOCUMENTS, 'files': {}}
        outcomes = value.setdefault('outcomes', {})
        if (not isinstance(outcomes, dict) or outcome_id in outcomes or len(outcomes) >= 10000
                or (state.data_dir / ('friday-unknown-' + hashlib.sha256(marker).hexdigest() + '.json')).exists()):
            return
        outcomes[outcome_id] = {'state': 'PENDING', 'route': route}
        check()
        _ordinary_commit(state, value, previous, journals=(('unknown', marker),))
    except Exception:
        return
    result = SendResult(success=False, error='document_outcome_UNKNOWN')
    status = 'UNKNOWN'
    try:
        await _ordinary_outcome_transcript(runner, session_id, 'PENDING')
        metadata = _thread_metadata_for_source(source, source.message_id) or {}
        metadata['_friday_document_outcome'] = (check, freeze_route(route))
        check()
        sent = await asyncio.wait_for(adapter.send(route['source']['chat_id'],
            'Доставка файла не подтверждена (UNKNOWN) или отклонена до отправки. '
            'Не отправляю его повторно без проверки результата.',
            reply_to=route['source']['message_id'], metadata=metadata), 30)
        if isinstance(sent, SendResult):
            message_id = sent.message_id
            confirmed = (sent.success is True and isinstance(message_id, str) and message_id.isascii()
                         and message_id.isdecimal() and int(message_id) > 0)
            status = ('CONFIRMED' if confirmed else 'UNKNOWN' if sent.error == 'document_outcome_UNKNOWN'
                      or sent.success is not False else 'FAILED')
            result = SendResult(success=confirmed, message_id=message_id if confirmed else None,
                                error=None if confirmed else 'document_outcome_' + status)
    except Exception:
        result = SendResult(success=False, error='document_outcome_UNKNOWN')
    if record_delivery is not None:
        record_delivery(result)
    try:
        check()
        candidate = copy.deepcopy(value)
        candidate['outcomes'][outcome_id]['state'] = status
        receipt = encoded({'schema': 'friday.ordinary-document-outcome.v1',
                           'outcome_id': outcome_id, 'route': route, 'state': status})
        _ordinary_commit(state, candidate, value, journals=(('candidate', receipt),))
        await _ordinary_outcome_transcript(runner, session_id, status)
    except Exception:
        # PENDING is durable and blocks another status when acknowledgement or
        # custody cannot be confirmed. Never trade that fence for a retry.
        return


async def _ordinary_outcome_transcript(runner, session_id, state):
    import time
    await runner.async_session_store.append_to_transcript(session_id,
        {'role': 'assistant', 'content': '', 'timestamp': time.time(), 'display_kind': 'hidden',
         'display_metadata': {'friday_file_delivery_observation': {'outcome': {'state': state}}}})


async def _ordinary_transcript(runner, session_id, relative, state, digest):
    """Keep host evidence out of assistant prose, retaining safe follow-up context.

    These presentation fields never authorize delivery: the durable native
    journal remains the only source for UNKNOWN/retry and route decisions.
    The empty hidden row is a private receipt, not an assistant utterance.
    Request projection omits it; public user/tool/MEDIA file anchors remain.
    Status authority stays in the journal. No unanswered user turn is manufactured
    on recovery.
    """
    import time
    observation = {'path': relative, 'sha256': digest, 'state': state}
    await runner.async_session_store.append_to_transcript(session_id,
        {'role': 'assistant', 'content': '', 'timestamp': time.time(),
         'display_kind': 'hidden',
         'display_metadata': {'friday_file_delivery_observation': observation}})


def bind_ordinary_document_source(event, source):
    """Freeze receiving SDK provenance before topic/session recovery can retarget.

    Missing proof keeps plain conversation available, but cannot authorize an
    ordinary local file effect. Called inside the already admitted native scope.
    """
    from gateway.admitted_ingress import admitted_ingress
    from hermes_cli.friday_user_scope import ordinary_file_scope
    cap = ordinary_file_scope()
    if cap is None or source.platform != Platform.TELEGRAM:
        return
    proof = admitted_ingress(event, source, '')
    if not isinstance(proof, dict):
        return
    message = proof.get('message', {})
    expected = {'bot_id': cap.principal[2], 'user_id': source.user_id,
                'chat_id': source.chat_id, 'thread_id': source.thread_id or '',
                'message_id': source.message_id}
    if (proof.get('platform') != cap.principal[0]
            or proof.get('transport_profile') != cap.principal[1]
            or proof.get('runtime_profile') != cap.profile
            or source.user_id != cap.principal[3]
            or any(message.get(k) != v for k, v in expected.items())):
        return
    source._friday_document_route = freeze_route({
        'transport_profile': cap.principal[1], 'runtime_profile': cap.profile,
        'bot_id': cap.principal[2], 'source': {'platform': source.platform.value,
            **{k:getattr(source,k) for k in ('chat_id','chat_type','user_id','thread_id','message_id')}}})
