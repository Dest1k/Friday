# Known XLSX recalculation with an isolated Always profile

The same synthetic workbook that failed under the default LibreOffice profile now has correct stored results after two real LibreOffice 26.2.5.2 resaves. All 12 cells and all six formula sources are correct in both outputs; formula caches are 14, 22, 38, 7, 37 and 22. The original 2061-byte input still contains stale 999 caches.

The [earlier default-profile control](../spreadsheet-known-xlsx-control/README.md) remains **FAIL**. Its actual installed default was `OOXMLRecalcMode=1` (`RECALC_NEVER`). The corrected operation seeded `OOXMLRecalcMode=0` (`RECALC_ALWAYS`) in **each fresh temporary isolated phase profile**. The input already had `calcMode=auto`, `fullCalcOnLoad=1` and `forceFullCalc=1`; changing the input or expected answers was unnecessary. The installed product configuration was not patched.

[STATUS.json](STATUS.json) separates accepted source, the actual synthetic run and product limitations. [SOURCE-NOTES.json](SOURCE-NOTES.json) links version-pinned LibreOffice source. The precise binary branch is inferred from that source and installed configuration; it was not instrumented inside the binary. Both conversions exited 0, both profile reads were observed, the process/network graph was reviewed and owned resources were closed. Raw traces, receipts, private package graphs and user-like workbooks are omitted.

## Inspect these exact artifacts without Office

From this directory, using Python 3 and its standard library:

```sh
python3 -I -B tools/verify_known.py --stale known-input.xlsx
python3 -I -B tools/verify_known.py first-resave.xlsx reopened.xlsx
```

The explicit [expected-values.json](expected-values.json) lists every input cell, formula and expected calculated value. Its historical `formula_evaluation` field is preserved byte-for-byte; actual settings are in STATUS. The verifier reads stored OOXML values and formulas, rejects changed cells, unsafe ZIP names and external relationships, and never evaluates formulas or launches Office. MANIFEST hashes all published files except itself.

## Reproduce the configuration change separately

`tools/seed_profile.py NEW_PROFILE_DIRECTORY` creates a new 0700 profile, writes the exact accepted 246-byte setting with exclusive creation, and refuses existing paths. [profile/user/registrymodifications.xcu](profile/user/registrymodifications.xcu) preserves the exact XML bytes. A diagnostic reproduction with your own matching LibreOffice binary can use the following recipe. **This recipe was not executed while preparing the capsule**, and does not reproduce the original containment/trace qualification.

```sh
# Set SOFFICE to your LibreOffice 26.2.5.2 soffice executable first.
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
mkdir "$work/input" "$work/out" "$work/reopened" "$work/home"
cp known-input.xlsx "$work/input/received.xlsx"
python3 -I -B tools/seed_profile.py "$work/profile-original"
python3 -I -B tools/seed_profile.py "$work/profile-resaved"
LC_ALL=C.UTF-8 HOME="$work/home" "$SOFFICE"   "-env:UserInstallation=file://$work/profile-original"   --headless --nologo --nodefault --nofirststartwizard --norestore   --convert-to 'xlsx:Calc MS Excel 2007 XML' --outdir "$work/out" "$work/input/received.xlsx"
LC_ALL=C.UTF-8 HOME="$work/home" "$SOFFICE"   "-env:UserInstallation=file://$work/profile-resaved"   --headless --nologo --nodefault --nofirststartwizard --norestore   --convert-to 'xlsx:Calc MS Excel 2007 XML' --outdir "$work/reopened" "$work/out/received.xlsx"
python3 -I -B tools/verify_known.py "$work/out/received.xlsx" "$work/reopened/received.xlsx"
```

The [archival source delta](source/recalculation-profile.patch) includes profile seeding in both host paths, exact setting/profile binding, observed profile-read requirements, and the distinct operation scope. SOURCE-MAPPING explains the removal of unchanged private path context. The private harness and authority inputs are intentionally not bundled; this patch does not install anything.

This accepted result is limited to the published 12-cell synthetic fixture, these formulas, this version and these temporary profiles. It establishes no visual review, broad formula-family acceptance, production configuration change, user-workbook acceptance or overall product acceptance. A dependent user-like file remains outside this result; none of its contents are published here. No Office, model call, Telegram send, installation or baseline was repeated to prepare this package.
