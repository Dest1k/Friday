# Source156: witness filename filter and R33 diagnostics

This checkpoint publishes one reviewed source change and selected aggregate measurements. Source review accepted the exact predicate reorder. The installed version was unchanged by this repair; product execution and functional acceptance remain NOT_RUN. Whole-path acceleration is not established.

The patch checks whether the run id occurs in a filename before calling `is_file()` in the witness inventory expression. All three directories are still enumerated afresh, and every matching filename still receives a fresh metadata probe. The selected file set and downstream owner, link, hash and current-state checks are unchanged. No cache or validator skip was added. [SOURCE-DELTA.patch](SOURCE-DELTA.patch) uses a synthetic neutral filename and contains only this expression change.

The isolated expression measurements were positive:

| Existing local check | Entries | Selected files | `is_file()` calls before → after | Median before → after |
| --- | ---: | ---: | ---: | ---: |
| Actual filesystem namespace | 5,178 | 18 | 5,178 → 18 | 58.849 → 7.193 ms |
| Independent filesystem fixture | 5,018 | 6 | 5,018 → 11 | 59.512 → 6.367 ms |

Each median uses five samples. Both checks retained the same selected set. These timings cover the isolated inventory expression; they provide no measurement of complete preparation, historical traversal, native composition, product execution or whole-path speed after the repair.

R33's original tester preparation failure remains preserved. It stopped at the existing 900-second preparation limit with `PreparationBudgetExpired`, before run creation or send. Product execution, postprocessing and reception are NOT_RUN. Total process wall time was 915.736 seconds, including 14.637 seconds of initial preparation outside the case clock. Measured preparation deadline lateness was 0.002879 seconds; the total process duration is not deadline lateness.

The material diagnostic interval completed; inventory remained incomplete at the cutoff. The retained counters are bounded observations. Their overflow leaves work unmeasured; unmeasured work, raised counts and scope completion must not be interpreted as zero. Nested phase timings and inclusive counter timings overlap and must not be added. [MEASURED-EVIDENCE.json](MEASURED-EVIDENCE.json) records the selected aggregates and these limits.

The source repair does not revise R33's result or authorize another operation. C34 is being assembled; no new operation has been selected. This archive supplies source and diagnostic evidence, with no installed or functional acceptance claim.

[SHA256SUMS](SHA256SUMS) covers the three public content files. Private source pins, closure references, absolute paths, machine and account identities, endpoints, credentials and user contents are excluded.
