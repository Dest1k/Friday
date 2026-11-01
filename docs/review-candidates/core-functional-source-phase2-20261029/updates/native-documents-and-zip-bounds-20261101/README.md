Native documents and bounded ZIP input

The ordinary file route gains bounded native reading for legacy DOC, XLS and EPUB. DOC exposes stored main-story text; XLS separates stored cell values from formula caches; EPUB follows declared XHTML reading order. These are explicit subsets, without rendering or macro execution. Their binary formats remain read-only.

The same source block adds DOCX/DOTX and ODT/OTT/FODT creation and preserving edits, plus inert DOCM/DOTM reads. Macro-profile mutation refuses. A shared ZIP member reader now bounds actual inflation, verifies sizes, CRC and stream completion, and rejects inconsistent local headers or data descriptors before native document parsing. Independent reviews and local consumer checks cover the composed source; original failures remain recorded.

Apply the 14-file patch after the spreadsheet-profile block from commit 250356d2a8735c9011a7ed2ff7116293273e1d33. Before/after hashes and exact patch replay were checked. Existing ODS, RTF, spreadsheet and presentation routes are retained.

This is reviewed source, not a deployed feature claim. The installed product remains Source117. Installation, Office, Telegram and live user acceptance remain separate pending work.
