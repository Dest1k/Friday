# Known XLSX recalculation control — FAIL

On 2026-11-01, the fixed LibreOffice 26.2.5.2 consumer opened, resaved and reopened a synthetic 12-cell XLSX under its declared consumer-default settings. Both processes exited successfully and resources were cleaned up. **All six deliberately stale formula caches remained 999 in both outputs**, although the formula sources were retained. Expected values were 14, 22, 38, 7, 37 and 22.

The runtime qualification therefore failed. The dependent Office check of the earlier received S18 file was **NOT_RUN**. Its historical model outcome remains UNKNOWN and its full observation remains incomplete. The earlier editable-PPTX preservation FAIL also remains unchanged. Accepted V01 presentation reading and continuation are separate results.

[STATUS.json](STATUS.json) records the fixed settings, runtime observations and limitations. [known-input.xlsx](known-input.xlsx), [expected-values.json](expected-values.json), [first-resave.xlsx](first-resave.xlsx) and [reopened.xlsx](reopened.xlsx) preserve the exact synthetic bytes for analysis. Private runtime logs and receipts are omitted; creator metadata in the exported workbooks is empty.

A temporary-directory mismatch had first refused the version probe before conversion. That failed operation was preserved. A minimal reviewed launcher fix allowed the distinct missing host stage under a new finite operation; no original clock, model call, Telegram send or artifact creation was replayed.

This result concerns this consumer-default invocation. It does not show that other LibreOffice settings cannot recalculate formulas, and it establishes no visual, broad formula-family or overall product acceptance.
