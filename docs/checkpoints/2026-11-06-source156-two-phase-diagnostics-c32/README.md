# Source156: bounded two-phase diagnostics (C32)

This checkpoint publishes a reviewed diagnostic source delta and selected measured facts. It establishes no product PASS, restored whole path, or whole-path acceleration. R31 remains closed and consumed with no run or send; product execution is NOT_RUN.

The patch adds bounded observation of exact retained partial/zero-wire validator code to the existing local native counters. Material and inventory have separate counter objects and lifetime ids 1 and 2, so inventory cannot overwrite the completed material result. Cleanup explicitly clears and verifies the owned code masks before clearing/freeing the monitoring tool. The original validator bodies, four native counter bodies, deadline, and acceptance criteria remain intact.

Independent review rejected the first diagnostic draft for two correctness defects:

- A start dropped by a bound could leave a reused frame id matchable. In 20/20 small-bound natural frame-reuse trials, a later return falsely completed an earlier failed proof. The repaired observer retires the old span before every bounded early return. All 20 repaired trials kept completed=0 and unresolved_spans=1; a row-bound control also retained the unresolved span.
- An incomplete scope was cached before all required closure joins succeeded, and later cache hits trusted mutable bindings. The repair publishes a scope only after authenticating every required local join and revalidates live code, namespace, defaults and closure identities on lookup. Incomplete, changed, or foreign scopes remain UNKNOWN while original validation still executes.

The original failures remain recorded in [MEASURED-EVIDENCE.json](MEASURED-EVIDENCE.json). Corrected source was independently reviewed after the reviewer fix. Its tests used exact extracted original validator/check code and real attach/phase seams on tiny owned inert fixtures under CPython 3.14.7. They did not run native history or the product.

Bounds per phase are 64 proof objects, 24 scopes, 64 proof rows, 256 active spans, and 256 inspected stack frames per proof event. There are at most four intermediate samples per phase and eight across both phases. Overflow and unsupported attribution remain explicit. A selected-CPython negative cleanup control observed masks still set after clear/free alone; corrected controls verified zero owned local masks and free tool slots.

The repaired observer added approximately 39.411, 50.184 and 68.520 microseconds per original call in three bounded inert configurations. These numbers describe observer cost on fixtures; they do not estimate actual-history cost or demonstrate an operational speed improvement.

R31's earlier actual preparation measurements are preserved separately:

| Observation | Result |
| --- | ---: |
| R29 material component | 406.153726 s |
| R31 material component, completed | 329.505506 s |
| R31 inventory until cutoff, incomplete | 133.840803 s |
| Existing preparation cutoff | 900 s |
| Initial preparation, outside the case clock | 15.605550 s |
| Total wrapper, including initial preparation | 916.698200 s |

The material comparison is component-only. Inventory stopped with PreparationBudgetExpired and its call counts were not collected. The wrapper includes the initial preparation interval outside the case clock; its total does not mean the preparation deadline was 16.7 seconds late. Inclusive nested timings must not be added. Raised counts are unmeasured, not zero. R31 predates this diagnostic delta and supplies no execution evidence for its new per-proof/inventory observer.

The later exact C32 Source156 package received source review and limited local qualifications. Current returned CURRENT156_ROLE_ROUTE_QUALIFIED in 69.046076 seconds. The unchanged partial semantic binder returned on ordinary, F-02 and raw_historical routes in 43.293355 seconds, with all three stale-pin negative controls refusing as expected. These overlapping qualification intervals must not be added. They establish the stated Current and partial source bindings only: full historical traversal, the full wrapped preparation path, future resource/dispatch checks, and product semantic acceptance remain separate unqualified boundaries.

[SOURCE-DELTA.patch](SOURCE-DELTA.patch) compares the original C31 counter/caller snapshots with the reviewed two-file diagnostic snapshot. Its headers use logical relative paths. A later source-reference rebind in the qualified C32 composition is outside this patch. The full package and unrelated internal sources are not reproduced. Exact before/after digests and package/composition digests are in the measured evidence. This is an archival source delta, not an installer or execution command.

[SHA256SUMS](SHA256SUMS) covers the three public content files. Local paths, raw receipts, machine/account/process identities, addresses, credentials and user contents are excluded from this selected summary.
