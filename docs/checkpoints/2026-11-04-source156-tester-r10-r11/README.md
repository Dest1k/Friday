# Source156 tester: R10–R11

Additive evidence snapshot: 4 November 2026, 20:48:29 Moscow time. Publication parent: `ae9ea1b56e4ab5d22dd82c0fbc28ee1bb44742ff`.

The candidate-r5 tester correction passed the physical-reader refusal seen in R10, but the actual complete F03 caller still failed in native preparation before a Run or request was created. R11 ended after 1284.305 seconds with zero sends and product result `NOT_RUN`. Functional, semantic and full/mass acceptance remain incomplete. This checkpoint establishes no successful-path speedup or user PASS.

| Actual attempt | Separate measured intervals | Outcome |
| --- | --- | --- |
| R10 | Parent 48.809834 s; caller 48.564236 s, containing initial preparation 11.799715 s and outer preparation 36.764521 s. Registration 0.207944 s is separate. | Physical-policy refusal: only `c_safe_read` mismatched. Before CAPTURE, native admission, claim, Run or send; `NOT_RUN`. |
| R11 | Parent 1284.305250 s; initial preparation 11.689953 s; outer preparation to native dispatch intent 286.491260 s; dispatch intent to stop request 985.896849 s and to parent reap 986.035113 s. | Passed the former physical-reader refusal, consumed admission, then remained in native prewire. Controlled cancellation after the original outer deadline; no native Run, send or completed-result receipt; `NOT_RUN`. |

These are nested or overlapping measured intervals, with different boundaries; do not add them together. R11's preparation-before-native-call proxy is 298.181213 seconds. Its stop request was 72.388766 seconds late relative to the original outer deadline. The original 1385-second parent limit did not expire. Exit 124 followed the stop signal through GNU timeout; it does not prove 1385-second expiry. The original clock was retained.

The [observations](OBSERVATIONS.json) distinguish R11's captured pre-call counters from the unreturned native call. Only the last completed scopes were captured: the 986-second native interval has no returned counters. Request, response, receive and result-processing durations remain unavailable. Post-reap reconciliation accepted closure with no Run or send and no owned resources remaining. It does not claim an inventory observation before the stop signal. The consumed admission is preserved and cannot be replayed.

The [source delta](s17-physical-reader.delta.txt) is a frozen, partial source-analysis text. It shows the source-owned callback binding and the paired omission of the conflicting inner observer and ancestor memo under the authenticated outer history owner. The legacy path retains both outside that owner. The full ancestry walk and surrounding history/proof/native/file/namespace checks remain in the original composition. The published text omits private dependency bindings and the composition adapter; it is neither executable source nor an installation candidate. Original source hashes and extraction details are in [MANIFEST.json](MANIFEST.json).

[Controls and their limits](CONTROLS.md) preserve the existing source-only findings. No test, qualification, model request or live operation was rerun to make this publication. Installed Source156, product source and services are unchanged by these materials. The earlier R7–R9 publication remains unchanged. Private paths, operational documents, authority, user content, identities and credentials are excluded; hashes identify retained private evidence without publishing it. This cut grants no future execution or retry.
