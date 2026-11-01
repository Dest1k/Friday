# Native format editing and attachment extraction candidate

This source-only joined candidate extends the accepted Source150 native tree with five related changes:

- Publisher `pub_text_edit` reads persisted page/story selectors and creates a new native copy with one equal-width literal text replacement.
- FB2 `fb2_edit` can select a specific persisted ordinal when text repeats. Existing unique-text editing remains available.
- Project reads passive native task catalogs from genuine MPP12 and MPP14 files. The existing bounded MPP9 task-name writer remains available.
- OneNote `onenote_text_edit` reads a current paragraph selector and creates a new native copy with one bounded equal-width text replacement. Existing history remains in the file.
- EML `eml_extract_attachment` creates a workspace file from one exact hash-bound native attachment, including a nonmultipart root attachment selected by `[]`.

Independent review of the exact joined bytes completed 78 unique local checks, including real read/edit/read/followup paths and negative controls for source identity, cancellation, publication uncertainty, selector validity and complete serialized response budgets. The OneNote and EML response-budget defects were fixed before publication; original failures and checker corrections are retained in private working evidence. Unchanged component review results were reused.

Coverage is intentionally bounded. Publisher Quill TOKN text is refused. Modern Project scheduling, dates, calendars and resources are not interpreted, and modern MPP writing and MPT are unavailable. OneNote editing is not redaction. Application interoperability, Telegram execution and user semantic acceptance have not run for this candidate. At the original source-only publication, Source151 composition still awaited the final Source150 carrier review and parent acceptance; installed Source117 and its permanent services had not changed.

Installation update, 2026-11-01: the corrected cumulative Source151 installation completed. Fresh selected native code and preservation of data were verified, then Gateway and Dashboard returned to permanent operation. [The installed checkpoint](INSTALLATION-20261101.json) records all 176 affected relative file hashes/modes, native identity, configuration hash and protected proof digests. The first failed installation remains recorded separately. Full B00 (170 original cases and 120 formats) is still in progress; no new Source151 live case result or semantic PASS is claimed. Initial harness refusals and product limitations remain visible. [The original source-only observations](OBSERVATIONS.json) remain historical and are not overwritten.

The patch carries the existing MPL/LGPL provenance and the new OneNote editing NOTICE. No fixture files, private workspaces, handoff files, credentials or user inputs are included.
