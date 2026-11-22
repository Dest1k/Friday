"""Bind one protected closed receiving window to its durable paired observations."""

from hashlib import sha256
import json
import math
import re
import time

from hermes_cli.friday_native_state import observe_commit_return
from hermes_cli.plugins_state import _invalid_storage_constant, _unique_storage_object

from .admission import (KEY, _PAYLOAD_KEY, IngressAdmissions, _IngressPairCommit, _PAIR_COMMIT_SEAL,
                        _pair_sha256, _payload_map, _receipt_document)

_ROUTE = frozenset(("session_key", "source_profile", "transport_profile", "runtime_profile"))
_WIRE = frozenset(("state", "reason", "generation", "target_update_ids",
                   "wire_updates_observed", "next_offset", "empty_boundary"))
_ID_LIMIT = 2**63


def _integer(value, minimum=1):
    return type(value) is int and minimum <= value < _ID_LIMIT


def _time(value):
    return type(value) in (int, float) and 0 <= value < _ID_LIMIT and math.isfinite(value)


def _wire_ids(raw, digest, *, generation, armed_at, cutoff, expires, maximum):
    if (type(raw) is not bytes or not 0 < len(raw) <= 16384 or sha256(raw).hexdigest() != digest):
        raise ValueError("unbound_wire_buffer")
    window = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_storage_object,
                        parse_constant=_invalid_storage_constant)
    if (type(window) is not dict or set(window) != _WIRE
            or window["state"] != "LOCAL_WIRE_CLOSED" or window["reason"] is not None
            or not _integer(generation) or type(window["generation"]) is not int
            or window["generation"] != generation):
        raise ValueError("wire_window_not_closed_or_wrong_generation")
    boundary = window["empty_boundary"]
    if (type(boundary) is not list or len(boundary) != 2
            or not all(_time(t) for t in (armed_at, cutoff, expires, *boundary))
            or not armed_at < cutoff <= boundary[0] <= boundary[1] < expires <= armed_at + 600):
        raise ValueError("unbound_empty_poll_boundary")
    ids = window["target_update_ids"]
    count, offset = window["wire_updates_observed"], window["next_offset"]
    if (type(ids) is not list or not _integer(count, 0) or not len(ids) <= count <= maximum
            or not _integer(offset, 0) or not all(_integer(i) and i < offset for i in ids)
            or any(left >= right for left, right in zip(ids, ids[1:]))):
        raise ValueError("unbound_wire_update_inventory")
    return tuple(str(i) for i in ids)


def _resolution(identity, *, matching=None, issues=(), reason=None):
    complete = matching is not None
    return {"state": "WIRE_RECEIPT_PAIRS_RESOLVED" if complete else "WIRE_RECEIPT_PAIRS_UNRESOLVED",
            "store_identity": identity, "observations": matching, "unresolved": tuple(issues),
            "reason": reason}


def _read_pairs(admissions, lock_deadline, protected_reader):
    state = admissions._payload_state()
    deadline = time.monotonic() + 2
    if lock_deadline is not None:
        if not _time(lock_deadline):
            raise ValueError("invalid_receipt_store_lock_deadline")
        deadline = min(deadline, lock_deadline)
    if protected_reader is None:
        doc, identity = state._read_storage_readonly(
            lock_deadline=deadline, with_identity=True, strict_json=True
        )
    else:
        doc, identity = protected_reader(state, deadline)
    if admissions._payload_state() is not state:
        raise PermissionError("wire_receipt_store_scope_changed")
    receipts = _receipt_document(doc.get(KEY, {"schema_version": 1, "receipts": {}}))["receipts"]
    payloads = _payload_map(doc.get(_PAYLOAD_KEY, {}), receipts)
    return state, identity, receipts, payloads


def _index_receipts(receipts, wanted, peer):
    bound = {update: [] for update in wanted}
    foreign = set()
    for key, receipt in receipts.items():
        if receipt["platform"] != "telegram":
            continue
        message = receipt["message"]
        update = message["platform_update_id"]
        if update not in bound:
            continue
        if message["bot_id"] == peer:
            bound[update].append((key, receipt))
        else:
            foreign.add(update)
    return bound, foreign


def _resolve_one(update, candidates, foreign, proofs, *, route, tester, state, identity, payloads,
                 armed_at, expires):
    if not candidates:
        return None, "wrong_receiving_bot" if update in foreign else "no_receipt_in_closed_store_buffer"
    if len(candidates) != 1:
        return None, "duplicate_receiving_update"
    (key, receipt), = candidates
    message = receipt["message"]
    message_id = message["message_id"]
    if (receipt.get("chat_type") != "dm"
            or any(receipt[field] != value for field, value in route.items())
            or (message["user_id"], message["chat_id"], message["thread_id"]) != (tester, tester, "")
            or re.fullmatch(r"[1-9][0-9]{0,18}", message_id) is None or int(message_id) >= _ID_LIMIT):
        return None, "wrong_receiving_route"
    if key not in payloads:
        return None, "legacy_receipt_without_paired_witness"
    payload = payloads[key]
    if not proofs:
        return None, "paired_bytes_without_successful_writer_return"
    if len(proofs) != 1:
        return None, "duplicate_commit_evidence"
    proof, = proofs
    if proof.receipt_key != key or proof.pair_sha256 != _pair_sha256(receipt, payload):
        return None, "committed_pair_drift"
    try:
        durable = observe_commit_return(state, proof.durable).commit
    except (RuntimeError, AttributeError):
        return None, "foreign_or_unproved_commit"
    if (durable.directory != identity["directory"] or durable.lock_inode != identity["lock_inode"]
            or not armed_at <= durable.closed_at < expires):
        return None, "commit_outside_bound_window_or_store"
    return (receipt, payload), None


def read_closed_wire_receipts(admissions, *, wire_bytes, wire_sha256, generation, armed_at, cutoff,
                              expires, scenario, route, committed_pairs, held_update_ids, lock_deadline=None,
                              _protected_reader=None):
    """Use one verified store read. Expose matcher inputs only for complete coverage.

    The native owner supplies the actual bound wire pin, route, arm/cutoff/expiry
    and successful returns from record_payload_commit on the same PluginState.
    The owner's existing dispatch boundary supplies any held or re-held IDs
    for this closed window. Held IDs always veto an otherwise valid pair.
    The gateway's private post-rights reader supplies the same verified buffer
    instead of opening the routed store a second time.
    """
    if (type(admissions) is not IngressAdmissions or type(scenario) is not dict
            or not _integer(scenario.get("peer_id")) or not _integer(scenario.get("tester_id"))
            or scenario["peer_id"] == scenario["tester_id"]
            or type(scenario.get("max_updates")) is not int or not 1 <= scenario["max_updates"] <= 200
            or type(route) is not dict or set(route) != _ROUTE
            or any(type(v) is not str or len(v) > 512 or "\x00" in v for v in route.values())
            or not all(route[key].strip() for key in _ROUTE - {"source_profile"})
            or type(committed_pairs) not in (list, tuple)
            or len(committed_pairs) > scenario["max_updates"]):
        return _resolution(None, reason="invalid_closed_wire_join_binding")
    try:
        wanted = _wire_ids(wire_bytes, wire_sha256, generation=generation, armed_at=armed_at,
                           cutoff=cutoff, expires=expires, maximum=scenario["max_updates"])
    except (ValueError, RecursionError):
        return _resolution(None, reason="invalid_or_unpinned_closed_wire")
    if (type(held_update_ids) not in (list, tuple) or len(held_update_ids) > len(wanted)
            or not all(_integer(update) for update in held_update_ids)):
        return _resolution(None, reason="unbound_held_update_inventory")
    held = {str(update) for update in held_update_ids}
    if len(held) != len(held_update_ids) or not held.issubset(wanted):
        return _resolution(None, reason="unbound_held_update_inventory")
    selected_proofs = {update: [] for update in wanted}
    for proof in committed_pairs:
        if (type(proof) is not _IngressPairCommit or proof._seal is not _PAIR_COMMIT_SEAL
                or proof.update_id not in selected_proofs):
            return _resolution(None, reason="foreign_or_unselected_commit_evidence")
        selected_proofs[proof.update_id].append(proof)

    try:
        state, identity, receipts, payloads = _read_pairs(admissions, lock_deadline, _protected_reader)
    except (OSError, RuntimeError, ValueError, TypeError):
        return _resolution(None, reason="verified_receipt_store_unavailable")
    peer, tester = str(scenario["peer_id"]), str(scenario["tester_id"])
    candidates, foreign = _index_receipts(receipts, wanted, peer)
    matching, issues = [], []
    for update in wanted:
        if update in held:
            issues.append((int(update), "held_receiving_update"))
            continue
        pair, problem = _resolve_one(update, candidates[update], foreign, selected_proofs[update],
                                     route=route, tester=tester, state=state, identity=identity,
                                     payloads=payloads, armed_at=armed_at, expires=expires)
        if problem is not None:
            issues.append((int(update), problem))
        else:
            matching.append(pair)
    return _resolution(identity, issues=issues) if issues else _resolution(identity, matching=tuple(matching))
