# Later tester observations: R7–R9

Dated delta: 4 November 2026, Moscow time; evidence snapshot `2026-11-04T19:05:49.284024+03:00`. This additive update describes the accepted candidate-r3 tester source and later observations. The original R4 failure and all earlier checkpoint files remain unchanged. Statements below update current status without rewriting the historical reports.

Source156 remains installed; this delta changes no product, service or installed source. The common tester source was accepted separately from runtime and user acceptance. Its exact Current qualification took 45.443 seconds and its three unchanged partial binder routes took 19.070 seconds. Those source qualifications establish neither a successful full common path nor a user PASS.

| Observation | Measured interval | Outcome |
| --- | --- | --- |
| R7 actual history preparation | Parent 182.072 s; caller 181.698 s, containing initial 11.833 s and outer 169.865 s | Protected-reader ownership refusal before native admission, Run or send; product `NOT_RUN`. |
| R8 Root source adoption | Caller 0.096543 s; parent 0.208816 s | Missing canonical consumer in the Root adoption input, before the case clock. This input defect was corrected separately; product `NOT_RUN`. |
| R9 actual full caller | Parent 48.707187 s; caller 48.479765 s, containing initial 11.820085 s and outer 36.659680 s | Nested physical-reader policy guard refused before CAPTURE, native admission, claim, Run or send; product `NOT_RUN`. |

The intervals are nested and must not be added together. R7 and R9 reached different refusal points. Their durations establish no successful-path speedup, request latency or response quality. R9 did not reach the capture/result telemetry point, so build, hit and fallback counters were not established.

R9's process was reaped, the exact owned foreground was released and reconciliation confirmed zero owned resources. Native inventories and cursor were unchanged; prior effects and clocks remain preserved. The precise mismatched reader identity remained unknown in this snapshot. The measured refusal does not prove a product failure.

The [source excerpt](closed-history-lifetime.py.txt) shows the accepted outer history-preparation lifetime, nested-reader handling and unchanged physical-reader identity guard. It is an unbound, non-executable review extract with imports, helper definitions and operational bindings omitted. Definitions were parsed and compiled as text only; no source was imported or executed. [MANIFEST.json](MANIFEST.json) records full original-source hashes, exact extraction locations, transformations and public hashes. [OBSERVATIONS.json](OBSERVATIONS.json) preserves the distinct measured intervals and evidence boundaries. [PUBLICATION-CHECKS.json](PUBLICATION-CHECKS.json) covers only publication privacy, syntax and provenance.

At this snapshot, repair of the same common path continued. A future candidate-r4 had not been accepted or published here. Functional and semantic acceptance remained unfinished, with no new successful user result and no mass acceptance. The earlier full B00 obligation remains open. Nothing in this delta authorizes a retry or execution.
