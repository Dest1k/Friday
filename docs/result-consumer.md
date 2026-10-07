# Parent result inspection and delivery

This source candidate extends the existing Friday association and native Hermes
plugin APIs. It adds no task engine, transport, polling loop or worker replay.
The operator must explicitly enable `settings.results: {enabled: true}` in the
Friday plugin entry, as well as the existing native injection/work/delivery
capabilities. No deployed profile is changed by this source package.

After independently observed worker quiescence, one notification is reserved
durably before it is scheduled through native `PluginContext.inject_message`.
The added optional `expected_session_id` parameter pins the original parent.
Native dispatch refuses a replacement session after `/new`; the existing strict
turn fence also checks a reset after queuing. `SCHEDULED` means only accepted by
the scheduler. Only an authenticated parent inspection records `OBSERVED`.
An uncertain notification is retained without automatic resend.
Pinned notifications also belong to their originating plugin load. Native dispatch
checks current consent, enabled state, gateway ownership and user authorization
after resolving the session and before adapter or model entry, including the
busy-session FIFO. Unload permanently retires that load's pending notifications;
loading the plugin again cannot revive them. Already admitted model turns are
outside this notification fence. A revoke and regrant entirely between checks is
not a durable revocation event; current settings are checked at each boundary.

The `friday_result` tool derives ownership from the actual native call and
session/profile context. Its reference and paths select owned content, not
authority. `list` enumerates bounded regular files in the quiescent DSH workspace;
`inspect` freezes a selected manifest into private staging and reads the checked
bytes. Absolute, hidden, escaping, linked, duplicate and oversized inputs are
refused. Files have stable names, lengths and hashes; later delivery rereads
those exact staged bytes. A retained manifest cannot be silently replaced.
Copying holds a separate, nonblocking per-task file lock. A competing inspection
refuses before copying; it does not hold the association/control lock. Retained
and orphan files share a ceiling of 32 entries and twice the configured total
artifact bytes. Failed evidence remains intact and consumes that allowance.

`assess` records the original parent's judgment together with references to its
actual file reads. Its method is explicitly `parent_file_review`. Text previews
are limited to 4096 bytes; incomplete or binary previews cannot support PASS.
Execution completion or worker prose does not establish the goal. If the goal
requires a test or environment check the parent has not observed, it must record
UNKNOWN. The finite fixture extension below does not establish an arbitrary executed-test
goal and currently lacks its required real owner PASS/FAIL gate. An assessment is
retained once before delivery; there is no automatic later upgrade.

`deliver` runs on the existing owned gateway-work API and uses the original
bot/chat/topic/reply binding. Each artifact is reserved as UNKNOWN before an
external await. Only a matching native acknowledgement establishes DELIVERED.
Explicit retries are allowed only after a proven pre-send rejection. A timeout,
cancellation, post-send exception or lost acknowledgement stays UNKNOWN; reload
or another call cannot silently resend it. Partial/stopped output and absent
goal checks remain explicit in the caption. Retrying delivery never starts DSH.
The caption uses the current stop/assessment snapshot from the durable send
reservation, taken after the awaited staging read.

The paired native deltas distinguish preflight refusal from an exception after
entering document delivery, and preserve pending Telegram updates on a polling
conflict when `drop_pending_on_cold_boot: false` is configured. That policy stops
the conflicting consumer instead of entering a queue-dropping recovery path.
Default upstream behavior remains unchanged when the opt-in is absent.

Validation uses the real plugin manager, middleware, state, injection scheduler
and document API with explicit offline worker/Telegram fixtures. Actual Telegram
delivery, real model consumption, executed goal checks, A0 output binding,
restart/runtime gates and complete release acceptance remain NOT_RUN.

## Exact finite fixture checks (source candidate; runtime NOT_ADMITTED)

`check` takes only `action` and the existing result `reference`. It accepts no
fixture name, shell text, interpreter, paths, timeout, environment or admission
from the model. The operator must separately supply one disabled-by-default
`settings.fixture_check` mapping with exactly these fields:

- `enabled: true`, `fixture: coding_add|engineering_report`, and `reference`;
- `owner_sha256` and `task_sha256`: existing canonical digest of the exact
  association owner and complete original `host.binding`, including ingress,
  original native call, task content and runtime;
- `artifacts`: the complete already collected original artifact descriptors,
  in candidate order for coding, or settings/report order for engineering;
- `source_root`: the canonical reviewed checkout root; `pins`: SHA-256 of the
  fixed checker, original owner test and original app/input paths for that
  fixture only. This operator path is never a tool argument;
- `terminal_scope_sha256`: digest of the complete current explicitly bound
  native local terminal profile; `shell_init_reviewed: true`.

The current native profile must have `terminal.shell_init_files: []` and
`terminal.auto_source_bashrc: false`. A missing/refusal/foreign terminal scope,
active result/terminal output transform hook, revoked result consent, source or
artifact drift, stop intent, unload, or unfinished worker refuses admission.
Local terminal itself has host authority. The flag is operator consent to the
reviewed fixed launcher and shell policy, not a sandbox receipt. No profile,
backend, guard, supervisor or shell policy is changed by this plugin.

The existing store reserves one `fixture_execution` observation as UNKNOWN
before any dispatch. The original native middleware supplies all five CALL_FIELDS;
normal registry dispatch only forwards task/session, so the other three fields
are read from that authenticated middleware scope, never invented from args.
A durable reservation cannot be replayed with another call ID, after reload,
failed persistence, missing hook or an uncertain terminal outcome. This also
bounds one snapshot set per association. Files remain retained in the existing
private task staging tree; fixed pin/candidate snapshots are single-link files,
written exclusively, fsynced, and owner read-only. Maximum input is 64 KiB/file.
The fixed checker is copied with its exact reviewed fixture assets before launch;
its existing bwrap isolates the actual finite workload. Coding checker and its
original test remain unchanged. Engineering gains an opt-in JSON observation
mode; its existing default CLI, app, CSV and five owner assertions are retained.
The observation reports digests of bytes actually snapshotted inside `run`,
not a reread of input after execution.

The fixed CLI runs through `ctx.dispatch_tool('terminal', ...)`, with original
native task/session and fixed foreground timeout 10 seconds. No `_host_local`,
middleware skip, gateway `preexec_fn`, worker launch or retry is introduced.
Native terminal has its own existing backend retry behavior; immutable finite
checkers have no worker/task side effects. This is not a one-physical-process
claim if that native backend internally retries. The nested registry dispatch
has no post-tool hook. Only the real OUTER `friday_result` hook, matched to the
one-use trusted pending response, all five current native fields, exact args,
association revision, current owner/profile/admission and artifact bytes, can
persist the terminal observation. Hook loss or write failure remains UNKNOWN.
An unobserved pending response is explicitly PENDING_OUTER_HOOK, not PASS.
Read `status` before assessing. The persisted fixture observation has `call`,
`kind`, `files`, `at_unix`, `revision`, `admission_sha256`, `fixture`, `state` and
`native`; native retains the bounded exact terminal JSON plus its SHA-256.

Only completed native exit 0 and the authentic original owner-test transcript,
matching fixture artifact/owner digests, complete matching UTF-8/base64 channels,
and finite cleanup fields establish the fixture PASS. A complete owner failure
is FAIL; refusal, timeout, yield/background, truncation, masked/inconsistent raw
channels, missing tests, checker `accepted=true` alone or stale proof is UNKNOWN.
One canonical JSON string-body escaping layer may be decoded reversibly; native
raw remains retained and redaction markers are never removed. Plain CLI output
still passes through native redaction. No whole-output encoding suppresses it.
`owner_fixture_execution` assessment cites exactly that retained observation;
PASS/FAIL cannot upgrade an UNKNOWN or foreign observation. An operator-declared
fixture, or a retained fixture attempt, cannot fall back to file-review PASS. Existing file review
and worker/delivery states retain their separate meanings. Arbitrary goals have
no executed-test proof through these two exact fixtures.

Current offline gate is BLOCKED for actual owner PASS/FAIL in the required outer
sandbox: the host AppArmor bwrap profile stacks `unpriv_bwrap`, which denies
capabilities to children and prevents their inner bwrap namespace setup. Actual
native normal dispatch, middleware and outer hook ran and retained UNKNOWN;
no original owner tests ran there. This is not a failed arithmetic/report goal
and not acceptance. The source candidate must not be enabled or represented as
review-ready until the lead provides a supported compatible offline sandbox
without changing/bypassing host protection, then runs both actual owner fixtures
and process stop controls on the final bytes. Model, A0 worker, real gateway,
Telegram, install and release gates remain NOT_RUN. Helper and offline gate
limits are per-process; no aggregate cgroup quota or remote inference cessation
is claimed.
