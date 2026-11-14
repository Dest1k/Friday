Bounded native ODS same-format edit follow-on

The patch extends the existing ODS scalar editor to the already validated passive native Calc rich profile. It edits the original target cell bytes, keeps validation identity and enforces an existing supported integer-between constraint. Formula, repeated, merged, protected, ambiguous, active, external and unknown rich structures still refuse. The rich extension is numeric-only and ODS-only; existing plain scalar profiles retain their behavior.

Other XML bytes and member payloads stay unchanged. Formula and chart caches are preserved without recalculation and may be stale. Generic readback still discloses its existing unsupported structures and limited coverage. ZIP repacking may normalize zero external attributes, as the existing writer already does. Archive identity, rendering, layout fidelity and recalculation are not claimed.

Run the focused regression runner with explicit genuine basic and rich ODS inputs and an isolated source stand:

```sh
python3 -I -B test_sameformat_ods.py \
  --native-root "$ISOLATED_SOURCE_STAND" \
  --s01-ods "$BASIC_ODS" \
  --s11-ods "$RICH_ODS" \
  --report "$NEW_PRIVATE_REPORT"
```

The source stand must contain real product modules with empty `tools/__init__.py` and `hermes_cli/__init__.py` package initializers. The runner pins only its finite pure-parser closure; it refuses normal runtime initializers. The report must be a new file outside the source and input files, under an existing owned directory without group/world write permission. Report contents are private execution evidence; the runner writes no workbook derivatives.

Tests cover real direct/profile edit paths, byte preservation, existing validation, stale-cache disclosures and derived negative controls. These source checks establish no installation, actual ordinary returned file, application recalculation or user acceptance. Those require separate integration and execution on the exact resulting version.
