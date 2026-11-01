Native PDF, Word and spreadsheet capabilities

This source block follows d0b623995a72713b50bf1f1605b7feb4cdbe5a1d. It adds bounded PDF page selection, rotation and composition without rasterizing content; inert Word revision/comment views; DOCX reports with native TOC and page fields; source-version-bound paragraph edits; native XLSB stored-cell reads; and editable ODS column charts with bounded formula recalculation.

Word paragraph edits require the source_sha256 returned by the same read that supplied the paragraph number. A changed source refuses before rendering. Report TOC/page fields require refresh in a compatible office application; generating fields does not prove displayed values or layout. Word review extraction does not accept or reject revisions. XLSB caches are labelled and never evaluated. Unsupported active, encrypted or structural content is rejected or explicitly marked according to each bounded profile.

The combined native snapshot contains 54 files, including 17 changed files and 10 new modules over Source124. Local validation completed 352 pytest cases and 29 subtests; the original 40 ODS controls are embedded inside one of those cases and are not an additional disjoint count. A final additive guidance correction passed six targeted controls; the other 53 native files retained their checked bytes. Component reviews and final composition review are retained separately. Original failures and reviewer corrections remain recorded.

These are source results. Installed Source117 remains unchanged; installation, Office, Telegram and live user acceptance are pending.
