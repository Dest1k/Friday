# Qwen public-core-v1: PARTIAL aggregate checkpoint

This is a sanitized, aggregate-only copy of the existing offline baseline report. The run is **parked** in `NEEDS_QUIET_WINDOW` with control `pause=true`, `stop=false`. No generation, resume, live verification or new scoring was performed for this checkpoint.

- Completed, generated and scored: **668/673**; **5 not_run**.
- Errors: **7**, all **technical losses**.
- **3** attempts remain `LOST_RESPONSE_AFTER_CLIENT_REBOOT` with model outcome `UNKNOWN`.
- `full_model_baseline=false`; this is **not a full PASS**.

| Benchmark | Expected | Generated | Scored |
| --- | ---: | ---: | ---: |
| IFBench | 300 | 300 | 300 |
| GPQA Diamond | 198 | 195 | 195 |
| LiveCodeBench v6 | 175 | 173 | 173 |

[baseline.md](baseline.md) preserves the aggregate metrics, errors, denominators and limitations. Its only content change is replacement of the internal endpoint alias with `<internal-endpoint>`; the trailing blank line is normalized to satisfy Git whitespace checks. Its references to raw directories describe the original run; those directories are not part of this checkpoint.

[scoring.json](scoring.json) is byte-identical to the scanned aggregate source and contains scoring provenance and review SHA256 values, not raw reviews. [STATUS.json](STATUS.json) records the machine-readable checkpoint status. [SHA256SUMS](SHA256SUMS) covers the four published files.

No raw requests, predictions, reviews, run manifest, private prompts, user data or authorization material is included. This is an **offline report only**, not a backup of private evidence and not a source or runtime handoff.
