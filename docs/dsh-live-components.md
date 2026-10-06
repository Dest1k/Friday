# Finite native Harness component evidence

`scripts/check_dsh_live.py` is a test runner, not the Hermes coding adapter.
It launches the accepted complete Harness executable in an owned transient
user-systemd service. `RuntimeMaxSec`, `KillMode=control-group`, bounded stop,
and recorded cgroup membership cover detached descendants without a gateway.
Bubblewrap supplies an empty root with read-only `/usr`, donor, toolchain and
inputs, private PID/IPC/UTS/user namespaces, writable assigned fixture/home
and disposable `/tmp`. Host home, Codex credentials and user-manager sockets
are absent. Host networking remains available for the explicit local endpoint;
this is a file/process boundary, not an egress firewall.

Every inference case takes one authenticated load observation before admission.
Busy means `DEFERRED_BUSY`, without retry/polling. Only the designated local
key enters the native environment; it is absent from argv and reports. The
trusted host bootstrap drops manager environment before entering the PID
namespace; the inner bootstrap sets the exact native environment. Inputs
and observation scripts are copied into each private case before mounting.
The transparent fetch observer records route/model/output reservations and
actual response usage, without auth, prompt, response content or replacement
responses. It is measurement instrumentation, not an enforcement guard.

The profile remains `workspace-write` and native approval `ask`. An initial
coding fixture exposed an unavailable nested native sandbox: shell refused
unconfined execution, and escalation was refused without an approval channel.
Removing the outer test's `--disable-userns` did not make a nested bubblewrap
usable; the actual nested namespace denial is retained. No danger-full-access,
fake backend, alternative shell or host repair replaces the refused operation.
Coding repair/test acceptance is BLOCKED in this tested boundary. Successful
read-tool, child and summary cases do not change that result.

The direct component executable mounts the entire native headless/base profile,
holding only its automatic headless intake rows. It resumes an actual cold
parent session, calls the public native one-shot subagent seam or `compactNow`,
uses real local streaming, flushes native checkpoints and shuts down. Child
execution is sequential and has a depth cap. This proves a native child, not
model-authored delegation or background-child recovery. Manual compaction
proves actual summary and replacement persistence, not automatic pressure or
compression quality. Native headless `--session-id` then reopens the same home
and cwd; a fact present only in prior context must be returned without tools.

All cases share the original absolute package deadline. Provider output4096,
summary2048 and headroom4096 are explicit temporary reservations within the
observed context40960/input40954, not permanent server limits. Native session
replay preserves route/state, while the total job budget is owned externally;
there is no claim of a native headless total-budget API. Full Hermes/Telegram,
artifact delivery, product acceptance and a coding-job adapter remain outside
this component assignment.

Run with explicit `--case`, accepted `--node`/`--donor`, new private `--runtime`
and `--evidence`, original ISO `--deadline`, and finite `--seconds` (<=300).
`main`/`reopen`/`disconnect`/`stop` require a staged harmless `--brief`.
`child`/`compact`/`inspect` require the actual `--session-id`; continuation
reuses only the assigned `--existing-home` and `--existing-fixture`.
An existing output directory or report is preserved and refused. Cases record
process exit separately from completed-turn reason, component status and the
host's independent fixture check. A final event or exit0 alone is insufficient.
