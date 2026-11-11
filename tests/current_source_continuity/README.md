# Current-source continuity regressions

These are portable, source-only regressions for the authenticated current198
project root, the first native199 publication and the bounded ODS native200
continuation. Copy the five core Python files together into a repository test directory.
The code contains no installation-specific paths. All fixture inputs are explicit.

Use a Python environment that already has the selected native source's normal
Python dependencies, including `ruamel.yaml`. The tests do not install packages.
`--repo-root` supplies real `plugins/friday_rework` and `tools` modules;
`--helpers-root` optionally supplies the source candidate's two install readers.
It defaults to the repository root. The tests create a private synthetic home,
17,888 native inventory files and 477/479/481-file project inventories. Temporary
fixture trees are removed on exit. Each invocation writes a new immutable run
directory containing JSON evidence and the exact two selected reader snapshots.

For example, from a checkout containing this directory at `tests/current_source_continuity`:

```sh
PYTHON=/path/to/dependency-complete/python
NATIVE_FIXTURE=/path/to/declared/native-source
NATIVE_RECEIPT=/path/to/source199-receipt.json
NATIVE_RECEIPT_SHA256=caller_verified_receipt_sha256

"$PYTHON" -I -B tests/current_source_continuity/check_current_source_edges.py \
  --repo-root . \
  --native-dir "$NATIVE_FIXTURE" \
  --native-receipt "$NATIVE_RECEIPT" \
  --native-receipt-sha256 "$NATIVE_RECEIPT_SHA256"
```

The native directory is a fixture source dependency, never a process target.
For a source198 dependency tree with the two genuine Source199 replacement modules
provided separately, add `--native-overlay /path/to/source199-overlay`; it must
contain `hermes_cli/friday_dashboard_owner.py` and `friday_ordinary_gateway.py`.
The caller-pinned receipt authenticates both replacements and every imported
native dependency, checked before importing its code and again in provenance.
No native PASS or installed-state acceptance is inferred from these imports.

To reproduce the old R1 refusal, add `--mode pre-r1`. This executes the bundled,
exact original `current_native_source_successor_checked` function in the selected
reader's in-memory namespace. Its bundled SHA is checked; no source file changes.
After actual T1 writer afterimages it proves both the stale raw configuration pin
refusal and, with only the original config bytes restored, the independent full
marker afterimage refusal. The current mode executes all five actual writer
`prepare_afterimages` outputs for T1 and T2 and preserves the original CP facts.

The second-edge run also installs the bundled exact previously accepted R1
one-edge dispatch function in memory, proves that it refuses the actual prospective
v2 CP200 request for its context, then restores the selected current function.
This separates the new continuity capability from the earlier R1 repair.

For the second edge, add:

```sh
  --second-layer-root . \
  --second-native-after /path/to/two-file-stage \
  --publisher docs/checkpoints/2026-11-07-v3-original-context-repair/friday_v3_layer_publication.py
```

The layer root contains the exact ODS patch and manifest under `patches/hermes/`
(or the pair directly in that directory). The native afterimage directory contains
`tools/scoped_ods.py` and `tools/scoped_spreadsheet_conversion.py`. Beforeimages
come from `--native-dir`; all four hashes must match the reader's exact ODS pins.
The existing request builder must be adjacent to the publisher. Its real preflight
and generated v2 request must exactly match the fixture request. Its historical
four-layer default remains unchanged.

The actual publisher's `run` applies the real ODS patch with finite local
`git --no-optional-locks apply` calls, journals and publishes only into the private
fixture, and joins the actual explicit pre/postpublication readers and committed
DEFAULT spec/inspect readers. The two project roots are distinct. The retained
199 project can then disappear while 200 continues to validate. Third-edge,
prior-reference, configuration/seal, before/staged/journal tamper and rollback
controls remain refusals.

Add `--publisher-rollback` for a separate invocation that injects a failure after
the real final committed DEFAULT spec/inspect checks. The real publisher restores
all affected beforeimages/absence/modes, preserves original CP199 facts, and refuses
a second execution of that consumed transaction. The retained199 reader and origin
are selected explicitly to check the restored state. `--reuse-r1-negatives` skips
only the previously verified R1 tamper matrix; T1/T2 writer positives still execute.
Do not add overlapping run check counts together.

The authority seams are explicit: synthetic owner source/receipt resolution,
an in-memory read-only pre-existing principal, package-availability checks disabled,
and the publisher's gateway-running query reports synthetic STOPPED. The copied
200 manifest alone has `prerequisites={}` because its 198 historical layer names
are synthetic; the original manifest, exact real patch, file rows and before/after
sources are retained and reported. This does not validate the production
prerequisite bank, authorization/admission, worker observation, runtime execution,
model behavior, Office, services, or Telegram. Ordinary native gateway semantics,
configuration serializer, onboarding/UserScope checks, source composition, five-file
writer, request builder and publisher execute their actual whole functions.

Per process limits are 150 CPU seconds and 2 GiB address space. There is no network,
model, Node, Office, service control or installed-home mutation. Logs and run JSON
may contain caller-provided local source paths; publish the five core Python files and
this README, not private run evidence or snapshots.

The entry is named `check_` so ordinary pytest collection never imports its
explicit-CLI parser or starts an expensive fixture accidentally. The Python
entry bytes are identical to the independently executed frozen source.

`check_cp_v2_offline.py` is an additional small publisher regression with explicit
synthetic source/stopped authority. It checks raw request custody, real private
publication and rollback; it does not prove the native chain. Invoke it with
`--publisher docs/checkpoints/2026-11-07-v3-original-context-repair/friday_v3_layer_publication.py`
and `--evidence-dir /path/to/new/private-evidence-directory`. Its test functions
are identical to the executed 76-control CP benchmark; only the default publisher
path was made repository-relative. Keep all run evidence private.
