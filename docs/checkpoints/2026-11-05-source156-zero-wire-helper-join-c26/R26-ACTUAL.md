# C26 actual narrow check R26

The actual check ended at the original 540-second preparation cutoff. Its
process was reaped; the saved native error is `PreparationBudgetExpired`.
The product result is **NOT_RUN**, with no functional credit. The admission
was consumed and remains preserved, but no native Run, send claim or matching
send/receive witness existed. Root checked the unchanged cursor and fresh task
quiescence under the existing receiver locks, then released only its foreground
resource. The existing Qwen worker was retained. R26 will not be replayed.

| Phase | Wall seconds | CPU seconds | Outcome |
|---|---:|---:|---|
| Initial preparation | 13.550 | 13.464 | Returned |
| Common prepare and history | 241.438 | 239.366 | Returned |
| Native read-only continuation | 48.922 | 48.583 | Returned |
| Native new cursor | 80.894 | 80.335 | Returned |
| Native new material | 147.386 | 146.241 | Preparation deadline |

The bridge (210.891 seconds) and history scope (24.157 seconds) are contained
in common preparation; nested intervals must not be added twice. The process
wall time was 554.426 seconds. The preparation cutoff fired approximately
0.00655 seconds late, with approximately 659.993 seconds of the outer 1200-second
window remaining. Scenario and reply clocks never started. No limits changed.
There was no result reception or post-result processing to measure.

Saved R24 completed common/read-only/cursor phases took 304.627/105.455/82.549
seconds; R26 took 241.438/48.922/80.894 seconds. These observations use different
source/history compositions and do not isolate causal speedup. Both material
phases were interrupted, so their durations do not compare completed work.
No whole-path acceleration or functional success is established.

Bounded intermediate stack diagnostics were saved inside the native call.
Category call counters were not collected and unknown progress is not zero.
The next engineering step is a focused repair based on these saved observations,
not another unchanged long run. Mass acceptance remains unapproved.

[r26-actual.json](r26-actual.json) contains curated measurements and original
document digests. The separate [source checkpoint](README.md) remains frozen at
its stated earlier cutoff. `SHA256SUMS.actual` covers these two actual-result
files; the original `SHA256SUMS` covers the original source checkpoint.
