from __future__ import annotations
import asyncio,logging
logger=logging.getLogger(__name__)
class GatewayStartupMixin:
    async def _clear_resume_pending_for_claimed_obligations(
        self, claimed: list, *, require_success: bool = False
    ) -> list:
        """Clear resume flags and return rows safe to redeliver. Startup recovery is best-effort;
        runtime reconnect recovery (``require_success``) is stricter: if the session-store write
        fails the response must not be sent, or the turn could be resumed too."""
        sendable = []
        for row in claimed:
            session_key = row.get("session_key") or ""
            if not session_key:
                sendable.append(row)
                continue
            try:
                await self.async_session_store.clear_resume_pending(session_key)
            except Exception:
                logger.debug("clear_resume_pending failed for %s", session_key, exc_info=True)
                if require_success:
                    continue
            sendable.append(row)
        return sendable

    async def _claim_pending_obligations(self) -> list:
        """Claim recoverable delivery-ledger rows and clear their ``resume_pending`` flags (pure DB
        work, no sends). Must run INLINE BEFORE ``_schedule_resume_pending_sessions`` and the
        abandonable boot-send task: these sessions already produced their answer, so the resume path
        must not re-run (re-pay for) the turn however long the sends take. Mid-send / rejected rows
        carry a visible recovered-reply marker (gateway/delivery_ledger.py). Returns the rows.

        A session with a recoverable obligation already produced its answer — the turn completed and only
        delivery is owed — so clearing ``resume_pending`` here prevents the resume path from re-running (and
        re-paying for) a turn whose output we hold, regardless of how long the sends ahead of redelivery
        take (#91969). Flood-refused rows adopted inside their wait come back flagged ``adopted``: their
        flags are cleared here too, and ``_redeliver_claimed_obligations`` leaves them to the timer.
        """
        try:
            from gateway.delivery_ledger import ledger_enabled, sweep_recoverable
            if not await asyncio.to_thread(ledger_enabled):
                return []
            # Claim only rows whose exact transport owner is connected: platform-only filtering would spend
            # a disconnected bot's retry budget because another bot on that platform is online.
            _profile_adapters = getattr(self, "_profile_adapters", None) or {}
            _pval = lambda p: getattr(p, "value", str(p))  # noqa: E731
            _deliverable_targets = {(_pval(p), "default") for p in self.adapters}
            # Legacy rows (no adapter_profile) are unambiguous only without multiplexing; else fail closed.
            if not _profile_adapters:
                _deliverable_targets.update((_pval(p), None) for p in self.adapters)
            for _profile, _adapters in _profile_adapters.items():
                _deliverable_targets.update((_pval(p), _profile) for p in _adapters)
            claimed = await asyncio.to_thread(
                sweep_recoverable, None,
                deliverable_platforms={platform for platform, _ in _deliverable_targets},
                deliverable_targets=_deliverable_targets,
            )
        except Exception:
            logger.debug("delivery ledger sweep failed", exc_info=True)
            return []
        if not claimed:
            return []
        # Clear resume_pending for EVERY claimed row before any send: the answer is in the ledger.
        # Claiming already spent one of the row's redelivery attempts — the answer is in the ledger, so the
        # resume path must never re-run these turns (#91969).
        await self._clear_resume_pending_for_claimed_obligations(claimed)
        return claimed

    async def _redeliver_claimed_obligations(self, claimed: list) -> int:
        """Redeliver final responses for claimed rows (network half of the split): runs inside the
        bounded boot-send task, so a flood-limited send can be abandoned by the restore gate without
        reopening the turn-replay window. Returns the redelivered count."""
        # No early return on an empty claim: the boot sweep may have ADOPTED flood-refused rows that are
        # not due yet, and those still need their timer armed below.
        try:
            from gateway.delivery_ledger import RECOVERED_MARKER, mark_delivered, mark_failed
        except Exception:
            logger.debug("delivery ledger import failed", exc_info=True)
            await self._release_unsent_boot_claims(claimed)
            return 0
        redelivered = 0
        untouched = 0
        try:
            for index, row in enumerate(claimed):
                untouched = index
                if row.get("adopted"):
                    # Adopted at boot inside its flood wait: its resume flag is cleared with the others, and
                    # the timer armed below sends it once the platform's deadline has passed.
                    continue
                if self._startup_should_abort():
                    return redelivered
                adapter = await self._obligation_adapter(row)
                if self._startup_should_abort():
                    return redelivered
                if adapter is None:
                    untouched = index + 1
                    continue
                content = row["content"]
                if row.get("needs_marker"):
                    content = row.get("marker", RECOVERED_MARKER) + content
                metadata = {"thread_id": row["thread_id"]} if row.get("thread_id") else None
                # From this point the current send is uncertain even if cancellation interrupts it.
                untouched = index + 1
                try:
                    result = await adapter.send(chat_id=row["chat_id"], content=content, metadata=metadata)
                except Exception as send_err:
                    logger.warning("obligation %s: redelivery send raised: %s", row["obligation_id"], send_err)
                    result = None
                with _log_suppressed(logging.DEBUG, "delivery ledger update failed", exc_info=True):
                    if result is not None and getattr(result, "success", False):
                        await asyncio.to_thread(mark_delivered, row["obligation_id"])
                        redelivered += 1
                        logger.info(
                            "Redelivered recovered final response to %s:%s (obligation %s, attempt %d)",
                            row["platform"], row["chat_id"], row["obligation_id"], row["attempts"],
                        )
                    else:
                        await asyncio.to_thread(
                            mark_failed, row["obligation_id"], str(getattr(result, "error", "") or "send failed")
                        )
        finally:
            await self._release_unsent_boot_claims(claimed[untouched:])
        if self._startup_should_abort():
            return redelivered
        # Whatever is still waiting on a flood penalty or a retry backoff (adopted at boot, skipped as not
        # yet due, refused again just now) gets a timer, so no rejected reply waits for the next restart.
        with _log_suppressed(logging.DEBUG, "arming flood redelivery timers failed", exc_info=True):
            await self._arm_flood_timers_for_waiting_rows()
        return redelivered

