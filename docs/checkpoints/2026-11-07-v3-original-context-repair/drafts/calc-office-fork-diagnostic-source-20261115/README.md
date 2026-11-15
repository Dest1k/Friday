# Office fork-refusal diagnostic source delta

This source-only archive adds eight lines to `stopped()` so the exact existing
`RuntimeError("helper_unexpected_fork_or_catchpoint")`, with no prior error,
records the existing bounded `process_boundary_snapshot()` before the unchanged
refusal and save. A snapshot exception records its class only. Helper permissions,
first-error storage, stop handling and the snapshot implementation are unchanged.

The actual unexpected-fork caller remains **UNKNOWN**. GpgME is a source-route
hypothesis, without accepted runtime attribution. Absolute program counters and
module basenames cannot establish library identity. The existing snapshot keeps
at most 24 sanitized symbol/module frames and bounded numeric metadata; it does
not add arguments, environment, locals, full paths, document content, mappings or
build IDs. Missing symbols or limited unwinding can leave the caller unresolved.

The prior Office745 operation is closed and refused, with no completed model or
metric (`M = null`); this archive does not reopen it. Product224 is unchanged under
the parent checkpoint assertion. Source review does not establish an installed or
executed diagnostic, fixture success, Office permission or a working product feature.

## Exact prerequisites

- [Base native observer](../calc-current-font-environment-source-20261115/candidate/outer/deps/native_return_observer.py):
  SHA-256 `4eb25d42b9487b151d9014771d25b2eb19878410c58d748aa19b0187c9c9fd29`.
- [Helper source used by the archived checks](../calc-gdb-one-shot-lifetime-source-20261115/candidate/paper_helper_gdb.py):
  SHA-256 `6c7f293cb7636b34f747143b797f9e6601d96d83ff5e49a752446bbfff334b10`.

`source-delta.patch` reconstructs the archived candidate exactly from that base.
Its `before/` and `candidate/` headers preserve the original source layout.
The two check sources are byte-exact provenance copies, not standalone runners:
`tests/test_source_diagnostic.py` needs the original `before/` tree and hardcodes
the private helper-cache path; `independent_controls.py` hardcodes the original
private source and helper-cache paths. The public prerequisites above supply the
same source bytes, but those archived paths have deliberately not been rewritten.

## Evidence boundary

The pinned original package records 11 passing pure extracted-source checks; the
pinned independent review records 10 passing independent source controls. Those
results are reused, not rerun for this archive. They use synthetic metadata and
AST-extracted functions and do not establish actual GDB, helper or Office behavior.

Packaging verified source hashes, byte-exact copies, in-memory compilation without
import or execution, eight added lines with exact patch reconstruction, unchanged
AST outside `stopped()`, prerequisite links/hashes and the six-file allowlist.
No test, candidate, helper, GDB, Office, model, service or network operation ran.
[PUBLIC-MANIFEST.json](PUBLIC-MANIFEST.json) contains source and review provenance
pins and the hashes of the five other package files. Raw evidence and private
captured payloads are excluded. Publication and any live integration remain with Root.
