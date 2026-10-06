# Full native sandbox acceptance

This finite Sol verification package uses the complete separately staged Harness
deployment from FRW005-NATIVE-PAYLOAD-BUILD. It does not change a donor, a runner,
permission policy, the Linux runner chain, AppArmor, or the host guard. It is not
the production coding adapter.

The deployment manifest is pinned to
`624c2520ee65b2a1f4b32545a0710faa551514f994396fe487d5bd428a22873d`.
The static upstream Landlock launcher is a new artifact; the historical refusal
on the incomplete deployment stays closed. The public `LocalSandboxProvider`
starts with default configuration and empty internals. No backend/probe override
or fallback is injected. Every actual `confine()` report must say `full`.

Run from this isolated worktree with its original received assignment and budget:

```sh
python -B scripts/check_dsh_native_full.py --case enforcement
python -B scripts/check_dsh_native_full.py --case deadline
python -B scripts/check_dsh_native_full.py --case stop
```

Inspect the retained reports before the model case. The first case proves real
workspace create/read/rename/delete, outside create/modify denials, an outside
symlink denial, read-only workspace and temporary-directory denials, immutable
input denial, and inherited denial in a subprocess. The outer sandbox deliberately
makes `/job-home` writable: rejection there establishes inner policy enforcement.
The native provider is allowed to select Landlock automatically after its real
bubblewrap probe; an unusable or partial provider is failure, not acceptance.

The deadline and stop cases run a confined double-forked, detached writer.
Systemd enforces a four-second deadline or the caller explicitly stops the owned
unit after observing the native ready marker and descendant output. Both retain
the live invocation/cgroup and terminal observation. Cgroup emptiness and stable
output establish cessation; a stop exit of zero does not imply goal completion.

Only after all these reports pass:

```sh
python -B scripts/check_dsh_native_full.py --case coding
```

The model case has one fresh authenticated idle-load observation and one intact
headless Harness invocation with `workspace-write`, the default approval behavior,
and no session adoption. A tiny supplied Python addition defect must fail the
existing test, be repaired in `calculator.py`, and pass the unchanged test. Actual
native completed-turn evidence, process exit, tool results, final workspace bytes
and an independent real post-test are required together. Failed or ambiguous
execution stays failed; the helper does not retry.

All cases retain the existing systemd/bubblewrap boundary: a private PID/user/IPC/
UTS namespace, capabilities dropped, read-only inputs/staged runtime/host toolchain,
private writable fixture and home, temporary storage, no new privileges, cgroup
termination, bounded task/memory/CPU limits and a real per-case deadline. A host
bootstrap sanitizes manager credentials before entering the namespace. The model
route is the existing `http://192.168.1.78:8001/v1`, model `dispatcher`; context
40960, output 4096, summary 2048 and headroom 4096 are temporary test values.
The key is read from the established environment reference and never serialized.
Host networking is retained; this boundary does not claim an egress firewall.

Private `.runtime/frw005-native-full/` and `.evidence/frw005-native-full/` retain
all controls, fixture bytes, failed/terminal receipts and raw separated logs.
The final manifest, rather than this procedural document, records actual results
and exact candidate hashes. No Telegram consumer, legacy restart, model fallback,
product admission, installation or release is performed by this package.
