"""Bounded local wire evidence for one pre-authorized Telegram direct-message window.

An empty accepted poll begun at or after cutoff can close the local wire.
Dispatch outcomes and admitted receipt custody must be checked separately.
"""

import json
import math


def _finite_time(value):
    return type(value) in (int, float) and math.isfinite(value)


def _integer(value, *, minimum=1):
    return type(value) is int and minimum <= value < 2**63


def _unique_object(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate polling response member")
        result[key] = value
    return result


class DirectMessageWireWindow:
    def __init__(self, *, generation, user_id, first_offset, armed_at, expires, max_updates):
        if (not _integer(generation) or not _integer(user_id)
                or not _integer(first_offset, minimum=0)
                or not all(_finite_time(value) for value in (armed_at, expires))
                or not 0 <= armed_at < expires <= armed_at + 600
                or type(max_updates) is not int or not 1 <= max_updates <= 200):
            raise ValueError("Invalid finite Telegram receiver window")
        self.generation = generation
        self._user_id = user_id
        self._expected_offset = first_offset
        self._armed_at = armed_at
        self._cutoff = None
        self._expires = expires
        self._max_updates = max_updates
        self._last_completion = None
        self._wire_closed = None
        self._unknown = None
        self._count = 0
        self._target_ids = []

    def bind_cutoff(self, cutoff):
        """Pin the authenticated sender's original cutoff once it exists."""
        if (self._cutoff is not None or not _finite_time(cutoff)
                or not self._armed_at < cutoff < self._expires):
            raise ValueError("Invalid or already pinned Telegram receiver cutoff")
        self._cutoff = cutoff

    def lost(self, reason):
        """Invalidate an unclosed window on a failed or fenced native poll."""
        if self._wire_closed is None and self._unknown is None:
            self._unknown = reason

    def observe_response(self, *, generation, accepting, parameters, started, completed, result):
        """Read the ordinary polling request envelope without changing its return."""
        if self._unknown is not None or self._wire_closed is not None:
            return
        allowed = parameters.get("allowed_updates")
        timeout = parameters.get("timeout")
        if (accepting is not True or type(allowed) is not list or "message" not in allowed
                or not _integer(timeout)):
            self.lost("native_poll_generation_or_filter_unbound")
            return
        status, payload = result
        if (type(status) is not int or not 200 <= status < 300
                or type(payload) is not bytes or not 0 < len(payload) <= 1_000_000):
            self.lost("malformed_poll_result")
            return
        try:
            decoded = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object)
        except (ValueError, RecursionError):
            self.lost("malformed_poll_result")
            return
        if type(decoded) is not dict or decoded.get("ok") is not True:
            self.lost("malformed_poll_result")
            return
        self.observe(generation=generation, offset=parameters.get("offset"), started=started,
                     completed=completed, allowed=allowed, updates=decoded.get("result"))

    def observe(self, *, generation, offset, started, completed, allowed, updates):
        """Accept one already parsed success from the designated polling adapter."""
        if self._unknown is not None or self._wire_closed is not None:
            return
        if (type(generation) is not int or generation != self.generation
                or not _integer(offset, minimum=0) or offset != self._expected_offset
                or not _finite_time(started) or not _finite_time(completed)
                or not self._armed_at <= started <= completed < self._expires
                or self._last_completion is not None and started < self._last_completion):
            self.lost("poll_generation_offset_or_clock_unbound")
            return
        if type(updates) is not list:
            self.lost("malformed_poll_result")
            return
        if self._count + len(updates) > self._max_updates:
            self.lost("update_budget_exceeded")
            return
        highest = offset - 1
        target_ids = []
        for update in updates:
            update_id = update.get("update_id") if type(update) is dict else None
            if not _integer(update_id) or not highest < update_id < 2**63 - 1:
                self.lost("unbound_poll_update_order")
                return
            highest = update_id
            kinds = update.keys() - {"update_id"}
            if len(kinds) != 1:
                self.lost("unclassified_wire_update")
                return
            kind, = kinds
            if kind not in allowed or type(update[kind]) is not dict:
                self.lost("unclassified_wire_update")
                return
            if kind != "message":
                continue
            message = update["message"]
            chat = message.get("chat") if type(message) is dict else None
            chat_id = chat.get("id") if type(chat) is dict else None
            if (type(chat_id) is not int or not chat_id
                    or chat.get("type") not in ("private", "group", "supergroup", "channel")):
                self.lost("unbound_wire_chat")
                return
            if chat["type"] == "private" and chat_id == self._user_id:
                target_ids.append(update_id)
        self._last_completion = completed
        self._count += len(updates)
        self._target_ids.extend(target_ids)
        self._expected_offset = highest + 1
        if not updates and self._cutoff is not None and started >= self._cutoff:
            self._wire_closed = (started, completed)

    def snapshot(self, now, *, current_generation, accepting):
        """Project evidence without changing the epoch or extending clocks."""
        if not _finite_time(now) or now < self._armed_at or (
                self._last_completion is not None and now < self._last_completion):
            raise ValueError("Invalid Telegram receiver observation clock")
        if type(current_generation) is not int or current_generation != self.generation or accepting is not True:
            state, reason = "UNKNOWN", "native_poll_generation_or_filter_unbound"
        elif self._unknown is not None:
            state, reason = "UNKNOWN", self._unknown
        elif self._wire_closed is not None:
            state, reason = "LOCAL_WIRE_CLOSED", None
        elif now >= self._expires:
            state, reason = "UNKNOWN", "wire_closure_not_observed"
        else:
            state, reason = "OPEN", None
        return {
            "state": state,
            "reason": reason,
            "generation": self.generation,
            "target_update_ids": list(self._target_ids),
            "wire_updates_observed": self._count,
            "next_offset": self._expected_offset,
            "empty_boundary": self._wire_closed,
        }
