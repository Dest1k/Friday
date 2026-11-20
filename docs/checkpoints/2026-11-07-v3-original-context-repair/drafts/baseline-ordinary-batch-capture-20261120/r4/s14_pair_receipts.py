"""Join real S14 deliveries after original R4 and native upload custody checks."""
from hashlib import sha256
import re


EXPECTED = {"S14-Alder-Report.txt": "text/plain", "S14-Alder-Report.pdf": "application/pdf"}
BINDING = {"run_id", "scenario_sha256", "step", "sent_message_id", "sent_ids", "request_body_sha256"}
INGRESS_FIELDS = {"run_id", "scenario_sha256", "step", "request_body_sha256",
                  "tester_sent_message_id", "native_ingress_message_id",
                  "receiver_bot_id", "native_chat_id", "native_thread_id"}


class Unbound(ValueError):
    pass


def require(check, reason):
    if not check:
        raise Unbound(reason)


def digest(raw):
    return sha256(raw).hexdigest()


def join_pair(binding, route, ingress, observations, raw_updates, native, byte_read):
    """Pure evidence join using already verified protected R4 artifacts and native journal receipts.

    byte_read(observation) returns the immutable bytes verified by the caller.
    Run R4 verify_reply_custody on the exact closed run first. The caller also
    verifies the protected upload correlation and projects it to ingress.
    Telegram message and chat IDs are local to their two receiving endpoints.
    """
    require(set(binding) == BINDING and len(native) == 2 and len(observations) == 2, "pair_shape")
    source = route["source"]
    original = {key: binding[key] for key in ("run_id", "scenario_sha256", "step", "request_body_sha256")}
    original.update(tester_sent_message_id=binding["sent_message_id"],
                    native_ingress_message_id=source["message_id"],
                    receiver_bot_id=route["bot_id"], native_chat_id=source["chat_id"],
                    native_thread_id=source["thread_id"])
    require(set(ingress) == INGRESS_FIELDS
            and all(type(ingress[k]) is type(v) and ingress[k] == v for k, v in original.items()),
            "original_ingress")
    require(type(binding["sent_message_id"]) is int and binding["sent_message_id"] > 0
            and binding["sent_message_id"] in binding["sent_ids"], "original_ack")
    require(all(isinstance(v, str) and re.fullmatch(r"[1-9][0-9]*", v)
                for v in (route["bot_id"], source["chat_id"], source["message_id"]))
            and source["thread_id"] is None and route["bot_id"] != source["chat_id"],
            "exact_private_two_endpoint_route")
    indexed = {item.get("file_name"): item for item in native}
    require(set(indexed) == set(EXPECTED), "native_roles")
    pairs, ids, updates, file_ids, unique_ids = {}, set(), set(), set(), set()
    native_ids = set()
    for item in observations:
        metadata = item["advertised_document"]
        name = metadata["file_name"]
        require(name in EXPECTED and name not in pairs and metadata["mime_type"] == EXPECTED[name], "receiver_roles")
        require(item["kind"] == "document" and item["complete_artifact"] is True, "receiver_incomplete")
        require(all(type(item[key]) is type(value) and item[key] == value
                    for key, value in binding.items()), "capture_binding")
        mid, uid = item["message_id"], item["update_id"]
        require(type(mid) is int and mid > 0 and type(uid) is int and uid > 0 and mid not in ids and uid not in updates,
                "duplicate_message_or_update")
        update = raw_updates[uid]
        raw = update["message"]
        require(update["update_id"] == uid and raw["message_id"] == mid and raw["document"] == metadata,
                "raw_artifact_binding")
        require(str(raw["from"]["id"]) == str(raw["chat"]["id"]) == route["bot_id"]
                and raw["chat"]["type"] == "private" and raw.get("message_thread_id") is None
                and raw["reply_to_message"]["message_id"] == binding["sent_message_id"],
                "foreign_original_route")
        info = item["get_file"]
        fid, unique = metadata["file_id"], metadata["file_unique_id"]
        require(fid == info["file_id"] and unique == info["file_unique_id"] and fid not in file_ids
                and unique not in unique_ids, "duplicate_or_foreign_file_identity")
        data = byte_read(item)
        require(type(data) is bytes and len(data) > 0 and len(data) == item["bytes"] == metadata["file_size"] == info["file_size"]
                and digest(data) == item["sha256"], "receiver_bytes")
        receipt = indexed[name]
        native_id = receipt["message_id"]
        require(isinstance(native_id, str) and re.fullmatch(r"[1-9][0-9]*", native_id)
                and native_id not in native_ids, "duplicate_or_invalid_native_message")
        require(receipt["state"] == "DELIVERED" and receipt["kind"] == "document"
                and receipt["file_name"] == name and receipt["sha256"] == item["sha256"]
                and receipt["bytes"] == len(data)
                and receipt["bot_id"] == route["bot_id"] and receipt["chat_id"] == source["chat_id"]
                and receipt["thread_id"] == source["thread_id"] and receipt["reply_to"] == source["message_id"],
                "native_delivery_binding")
        ids.add(mid)
        native_ids.add(native_id)
        updates.add(uid)
        file_ids.add(fid)
        unique_ids.add(unique)
        pairs[name] = {"message_id": mid, "native_message_id": native_id, "update_id": uid,
                       "bytes": len(data), "sha256": digest(data)}
    return pairs
