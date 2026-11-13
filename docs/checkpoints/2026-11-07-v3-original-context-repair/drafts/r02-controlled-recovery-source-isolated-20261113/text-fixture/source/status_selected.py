from __future__ import annotations
import os
from pathlib import Path
START_TIME_DRIFT_TOLERANCE=200
def pid_exists_stdlib(pid):
    raise RuntimeError("Stand forbids non-source fallback; psutil required for liveness")
def start_time_fingerprints_match(recorded: Any, current: Any, tolerance: int = START_TIME_DRIFT_TOLERANCE) -> bool:
    """Liveness-reconciliation comparator for :func:`get_process_start_time` fingerprints: the
    recorded owner and the current reading are the same incarnation when they agree within
    ``tolerance``. Raises on junk; callers decide what an unreadable (``None``) side means."""
    return abs(int(current) - int(recorded)) <= tolerance

def _get_process_start_time(pid: int) -> Optional[int]:
    """Return a stable per-process start-time fingerprint, or None.

    Used as a PID-reuse guard: a ``(pid, start_time)`` pair uniquely identifies
    a process, so a recycled PID (same number, different process) yields a
    different value and is never mistaken for the original.

    On Linux this is field 22 of ``/proc/<pid>/stat`` (start time in clock
    ticks since boot, an int).  On platforms without ``/proc`` (macOS, Windows)
    we fall back to ``psutil.Process(pid).create_time()`` — a float epoch
    timestamp — quantized to an int (centiseconds) for stable equality.

    The two sources are never mixed on a single platform: ``/proc`` always
    succeeds first on Linux, and always fails on macOS/Windows so psutil is
    always used there.  Because the guard only compares the value recorded at
    spawn against the live value *on the same host*, the differing units across
    platforms are irrelevant — only same-source equality matters.
    """
    stat_path = Path(f"/proc/{pid}/stat")
    try:
        # Field 22 in /proc/<pid>/stat is process start time (clock ticks).
        return int(stat_path.read_text(encoding="utf-8").split()[21])  # windows-footgun: ok (/proc is BOM-free)
    except (FileNotFoundError, IndexError, PermissionError, ValueError, OSError):
        pass

    # No /proc (macOS / Windows): psutil is a hard dependency and exposes a
    # cross-platform creation time.  Quantize to centiseconds so repeated reads
    # of the same process compare equal without float-precision fragility.
    try:
        import psutil  # type: ignore
        return int(round(psutil.Process(pid).create_time() * 100))
    except Exception:
        return None

def get_process_start_time(pid: int) -> Optional[int]:
    """Public wrapper for retrieving a process start time when available."""
    return _get_process_start_time(pid)

def _pid_exists(pid: int) -> bool:
    """Cross-platform "is this PID alive" check that does NOT kill the target. CRITICAL on Windows:
    ``os.kill(pid, 0)`` sends ``CTRL_C_EVENT`` to the whole console group (bpo-14484), so prefer
    psutil, then ctypes ``OpenProcess`` (Windows) / ``os.kill(pid, 0)`` (POSIX). Zombies report
    dead: treating one as alive makes --replace wait forever under systemd Restart=always."""
    pid = int(pid)
    try:
        import psutil  # type: ignore
        # Best-effort zombie check: status-read failures fall through to pid_exists().
        # Windows has no POSIX zombies, and this probe costs ~7 ms per call — once per
        # registry entry inside the session file lock (#115578). Skip it on Windows and
        # let pid_exists() below (or the ctypes fallback) decide.
        probe_zombie = os.name != "nt"
        try:
            # A zombie (defunct) process is still in the process table, so ``psutil.pid_exists()`` returns
            # True for it — but it is already dead: SIGKILL has no effect and it cannot be a running
            # gateway. Treating a zombie as alive makes ``--replace`` wait for the old PID to die (it never
            # does, until its parent reaps it), then abort with exit 1 — a silent crash loop under systemd
            # ``Restart=always``, which respawns the gateway before reaping the previous process (issue
            # #42126). Report zombies as dead so the takeover proceeds. Best-effort: any failure to read
            # status (partial/stub psutil, access denied, transient race) falls through to the authoritative
            # ``pid_exists()`` below rather than raising.
            if probe_zombie and psutil.Process(pid).status() == psutil.STATUS_ZOMBIE:
                return False
        except getattr(psutil, "NoSuchProcess", ()):
            return False
        except Exception:
            pass
        return bool(psutil.pid_exists(pid))
    except ImportError:
        pass  # Fall through to stdlib fallback.
    return pid_exists_stdlib(pid)

