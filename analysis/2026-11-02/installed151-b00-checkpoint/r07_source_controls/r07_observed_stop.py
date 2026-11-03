"""Source-only R07 pre-publication observer; no product mutation or launcher."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import threading
from pathlib import PurePosixPath
from unittest.mock import patch


_STAGE = re.compile(r"\.friday-docx-[0-9a-f]{32}\Z")
_FIELDS = (
    "st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns",
    "st_mode", "st_nlink", "st_uid", "st_gid",
)


class ObservationRefused(RuntimeError):
    pass


def _identity(info):
    return tuple(getattr(info, field) for field in _FIELDS)


def _parent_identity(info):
    # Staging a new child legitimately changes directory size/mtime/ctime.
    # Keep the retained directory inode and ownership/mode pin, while the
    # product _check_parent continues to validate the logical workspace path.
    return tuple(getattr(info, field) for field in
                 ("st_dev", "st_ino", "st_mode", "st_nlink", "st_uid", "st_gid"))


def _renamed_identity(info):
    values = _identity(info)
    return values[:4] + values[5:]


def _stat_at(fd, name):
    try:
        return os.stat(name, dir_fd=fd, follow_symlinks=False)
    except FileNotFoundError:
        return None


class ObservedStopAdapter:
    def __init__(self, *, docx_module, web_context, check_cap, cap, call,
                 parent_fd, final_path, final_leaf, expected_principal,
                 expected_task_id, expected_call_id, expected_session_id,
                 hold_seconds=30.0, max_output=1_000_000):
        if final_leaf != PurePosixPath(final_path).name:
            raise ValueError("final_leaf_path_mismatch")
        if not 0 < hold_seconds <= 60 or not 0 < max_output <= 1_000_000:
            raise ValueError("observer_bounds_refused")
        self.docx = docx_module
        self.web_context = web_context
        self.check_cap = check_cap
        self.cap = cap
        self.call = call
        self.parent_fd = parent_fd
        self.final_path = final_path
        self.final_leaf = final_leaf
        self.expected_principal = expected_principal
        self.expected_task_id = expected_task_id
        self.expected_call_id = expected_call_id
        self.expected_session_id = expected_session_id
        self.hold_seconds = hold_seconds
        self.max_output = max_output
        self.ready = threading.Event()
        self.resume = threading.Event()
        self.move_finished = threading.Event()
        self.lock = threading.Lock()
        self.observation = None
        self.refusal = None
        self.stop_receipt = None
        self.stop_error = None
        self.stop_calls = 0
        self.move_returned = False
        self.move_error = None
        self.final_after_move = None
        self.stage_fd = None
        self._entered = False
        self._original_move = None
        self._patcher = None
        self._parent_identity = None
        self._final_report = None

    def __enter__(self):
        self._parent_identity = _parent_identity(os.fstat(self.parent_fd))
        self._original_move = self.docx._move
        self._patcher = patch.object(self.docx, "_move", self._observed_move)
        self._patcher.start()
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self._patcher is not None:
            self._patcher.stop()
        self._close_stage()

    def _close_stage(self):
        if self.stage_fd is not None:
            os.close(self.stage_fd)
            self.stage_fd = None

    def _refuse(self, reason):
        self.refusal = reason
        self.ready.set()
        raise ObservationRefused(reason)

    def wait_observed(self, timeout=None):
        bound = self.hold_seconds if timeout is None else timeout
        if not 0 < bound <= self.hold_seconds or not self.ready.wait(bound):
            raise TimeoutError("r07_observation_deadline")
        if self.refusal is not None:
            raise ObservationRefused(self.refusal)
        if self.observation is None:
            raise ObservationRefused("observation_missing")
        return dict(self.observation)

    def stop_and_resume(self):
        with self.lock:
            if not self.ready.is_set() or self.observation is None or self.refusal is not None:
                raise ObservationRefused("valid_observation_required")
            if self.stop_calls:
                raise ObservationRefused("stop_already_invoked")
            self.stop_calls += 1
            try:
                self.stop_receipt = self.call.stop()
            except Exception as error:
                self.stop_error = type(error).__name__
            finally:
                self.resume.set()
            return self.stop_receipt

    def _bind_call(self):
        self.check_cap(self.cap)
        if self.call.stopped.is_set():
            self._refuse("call_already_stopped")
        turn_stopped = getattr(self.call.turn, "stopped", None)
        if turn_stopped is not None and turn_stopped.is_set():
            self._refuse("turn_already_stopped")
        if self.web_context._current.get() is not self.call:
            self._refuse("current_call_mismatch")
        if not self.web_context.same_web_authority(self.call):
            self._refuse("principal_authority_mismatch")
        if getattr(self.call, "user_authority", None) != self.expected_principal:
            self._refuse("principal_pin_mismatch")
        expected = (self.expected_task_id, self.expected_call_id, self.expected_session_id)
        actual = (self.call.task_id, self.call.call_id, self.call.session_id)
        if actual != expected:
            self._refuse("task_call_session_mismatch")
        if self.call.session is not None or self.call.registry is not None:
            self._refuse("renderer_custody_still_bound")

    def _capture_stage(self, fd, stage):
        if not _STAGE.fullmatch(stage):
            self._refuse("stage_name_mismatch")
        final = _stat_at(fd, self.final_leaf)
        if final is not None:
            self._refuse("final_already_present")
        held = os.open(stage, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        self.stage_fd = held
        before = os.fstat(held)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                or before.st_uid != os.getuid() or before.st_mode & 0o077
                or not 0 < before.st_size <= self.max_output):
            self._refuse("stage_metadata_refused")
        named = os.stat(stage, dir_fd=fd, follow_symlinks=False)
        if _identity(before) != _identity(named):
            self._refuse("stage_inode_path_mismatch")
        digest = hashlib.sha256()
        size = 0
        while True:
            chunk = os.read(held, min(65536, self.max_output + 1 - size))
            if not chunk:
                break
            size += len(chunk)
            if size > self.max_output:
                self._refuse("stage_size_refused")
            digest.update(chunk)
        after = os.fstat(held)
        named_after = os.stat(stage, dir_fd=fd, follow_symlinks=False)
        if size != before.st_size or _identity(before) != _identity(after) or _identity(after) != _identity(named_after):
            self._refuse("stage_changed_while_observed")
        self.observation = {
            "stage": stage,
            "stage_fd": held,
            "stage_identity": dict(zip(_FIELDS, _identity(after))),
            "stage_sha256": digest.hexdigest(),
            "final_path": self.final_path,
            "final_absent_before_stop": True,
            "cap_checked": True,
            "current_call_match": True,
            "principal_match": True,
            "task_id": self.expected_task_id,
            "call_id": self.expected_call_id,
            "session_id": self.expected_session_id,
            "renderer_custody_released": True,
        }

    def _observed_move(self, source_fd, stage, destination_fd, leaf):
        if self._entered:
            self._refuse("duplicate_publication_move")
        self._entered = True
        try:
            if source_fd != self.parent_fd or destination_fd != self.parent_fd:
                self._refuse("parent_fd_mismatch")
            if _parent_identity(os.fstat(source_fd)) != self._parent_identity:
                self._refuse("parent_inode_mismatch")
            if leaf != self.final_leaf:
                self._refuse("final_leaf_mismatch")
            self._bind_call()
            self._capture_stage(source_fd, stage)
            self.ready.set()
            if not self.resume.wait(self.hold_seconds):
                self.refusal = "resume_deadline"
                raise TimeoutError("r07_resume_deadline")
            try:
                result = self._original_move(source_fd, stage, destination_fd, leaf)
                self.move_returned = True
                return result
            except Exception as error:
                self.move_error = type(error).__name__
                raise
            finally:
                self._record_final_after_move(destination_fd, leaf)
        except Exception as error:
            if self.refusal is None and self.observation is None:
                self.refusal = type(error).__name__
            self.ready.set()
            raise
        finally:
            self.move_finished.set()

    def _record_final_after_move(self, fd, leaf):
        try:
            named = os.stat(leaf, dir_fd=fd, follow_symlinks=False)
        except FileNotFoundError:
            self.final_after_move = {"present": False}
            return
        except OSError as error:
            self.final_after_move = {"present": None, "error": type(error).__name__}
            return
        held = os.fstat(self.stage_fd)
        self.final_after_move = {
            "present": True,
            "same_inode": (named.st_dev, named.st_ino) == (held.st_dev, held.st_ino),
            "renamed_identity_match": _renamed_identity(named) == _renamed_identity(held),
        }

    def finalize(self):
        if self._final_report is not None:
            return dict(self._final_report)
        if not self.move_finished.is_set() or not self.stop_calls:
            raise ObservationRefused("completed_stop_and_move_required")
        stage_info = _stat_at(self.parent_fd, self.observation["stage"])
        final_info = _stat_at(self.parent_fd, self.final_leaf)
        receipt_status = (self.stop_receipt or {}).get("status") if isinstance(self.stop_receipt, dict) else None
        stopped = bool(self.call.stopped.is_set())
        call_settled = self.call not in self.call.turn.calls
        failures = []
        unknown = []
        if final_info is not None or (self.final_after_move or {}).get("present") is True:
            failures.append("final_present_after_owned_stop")
        if (self.final_after_move or {}).get("present") not in (True, False):
            unknown.append("post_move_final_presence_unobserved")
        if receipt_status != "QUIESCENT" or self.stop_error is not None or not stopped:
            unknown.append("owned_stop_not_confirmed")
        if stage_info is not None:
            unknown.append("owned_stage_residual")
        if not call_settled:
            unknown.append("native_call_registry_residual")
        if failures:
            status = "FAIL_PUBLICATION_AFTER_OWNED_STOP"
        elif unknown:
            status = "UNKNOWN_STOP_OR_CLEANUP"
        else:
            status = "ISOLATED_OBSERVATION_COMPLETE_NOT_CASE_PASS"
        self._final_report = {
            "schema": "frw.b00.r07.observed-stop-observation.v1",
            "status": status,
            "observation": dict(self.observation),
            "stop": {
                "invocations": self.stop_calls,
                "receipt": self.stop_receipt,
                "error_type": self.stop_error,
                "call_stopped": stopped,
                "call_registry_settled": call_settled,
            },
            "move": {
                "returned": self.move_returned,
                "error_type": self.move_error,
                "final_after_move": self.final_after_move,
            },
            "cleanup": {
                "final_present": final_info is not None,
                "stage_present": stage_info is not None,
                "renderer_custody_released_at_stage": self.observation["renderer_custody_released"],
            },
            "failures": failures,
            "unknown": unknown,
            "source_recheck": "ROOT_SEPARATE_ORIGINAL_READ_AND_HASH_REQUIRED",
            "whole_case_credit": False,
            "live_original_healthy": "NOT_RUN_SEPARATE_MANDATORY",
        }
        self._close_stage()
        return json.loads(json.dumps(self._final_report, sort_keys=True))
