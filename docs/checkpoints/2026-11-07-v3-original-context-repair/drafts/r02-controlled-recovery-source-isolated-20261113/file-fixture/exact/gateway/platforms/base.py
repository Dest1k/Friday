from dataclasses import dataclass
from typing import Any, Optional
def _platform_name(platform) -> str:
    """Normalize a Platform enum / raw string into a lowercase name."""
    value = getattr(platform, "value", platform)
    return str(value or "").lower()


def _thread_metadata_for_source(source, reply_to_message_id: str | None = None) -> dict | None:
    """Platform-aware thread metadata for adapter sends. Telegram DM topics route with
    ``message_thread_id`` + a reply anchor; anchorless synthetic/resumed sends fall back to
    ``direct_messages_topic_id`` when supported."""
    thread_id = getattr(source, "thread_id", None)
    platform = _platform_name(getattr(source, "platform", None))
    metadata = {"thread_id": thread_id} if thread_id is not None else {}
    # Slack workspace identity is routing state: carry it so a multi-workspace Socket Mode
    # gateway never falls back to its primary WebClient.
    scope_id = getattr(source, "scope_id", None) if platform == "slack" else None
    if scope_id:
        metadata["slack_team_id"] = str(scope_id)
    if not metadata:
        return None
    if platform == "telegram" and getattr(source, "chat_type", None) == "dm":
        metadata["telegram_dm_topic_reply_fallback"] = True
        if str(thread_id) not in {"", "1"}:
            metadata["direct_messages_topic_id"] = str(thread_id)
        anchor = reply_to_message_id or getattr(source, "message_id", None)
        if anchor is not None:
            metadata["telegram_reply_to_message_id"] = str(anchor)
    # Routed profile (multiplex / profile_routes): outbound prune paths must not assume the
    # adapter's static profile stamp.
    profile = str(getattr(source, "profile", None) or "").strip()
    if profile:
        metadata["hermes_profile"] = profile
    return metadata


@dataclass
class SendResult:
    """Result of sending a message."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    # Adapter-specific metadata. Contract: Telegram edit-overflow partials set
    # raw_response["partial_overflow"] so the stream consumer sends the missing tail.
    raw_response: Any = None
    retryable: bool = False  # transient connection error — base retries automatically
    retry_after: Optional[float] = None  # server-requested delay (Telegram FloodWait) beats our backoff
    # Extra ids (send order) when a payload was split; ``message_id`` is then the LAST id so
    # later edits target the newest chunk.
    continuation_message_ids: tuple = ()
    # SEND_ERROR_KINDS member (failures only) via :func:`classify_send_error`, so consumers
    # branch without substring-matching ``error``.
    error_kind: Optional[str] = None

