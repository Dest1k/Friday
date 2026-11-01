Native spreadsheet profiles

This source adds XLSX/XLTX creation, reading and bounded numeric edits; inert XLSM/XLTM reading; and ODS/OTS/FODS creation, reading, scalar editing and conversion within the OpenDocument family. Mutation refuses active or externally linked content. Formula text and stored values remain distinct. Macro projects are never executed or edited.

The independent review repaired flat OpenDocument styles, media-type checks, external-content detection and worksheet/shared-string relationship handling. The seven-file patch retains the preceding ODS joins/merges and RTF routes. Apply it after the native ODS/RTF source block from commit 9e8ee098f8fe49ec85b66e656aabc9c4cb62bf64. Exact before/after hashes are in MANIFEST.json; the patch was applied to an isolated base and its resulting bytes verified.

Implementation, independent review and local route checks passed. These are source-only results: the installed product remains Source117. Installation, Office, Telegram and user acceptance remain pending. Local test counts overlap and are not summed as independent scenarios.
