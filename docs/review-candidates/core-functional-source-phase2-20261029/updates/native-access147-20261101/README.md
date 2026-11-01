# Native Access table reading — Source147

Adds bounded native reading of ordinary scalar tables in Jet4 MDB and ACE2007 ACCDB files through the existing scoped file reader. Real database fixtures cover complete 512-row tables, Unicode text and fixed-width fields. No database engine or SQL execution is used.

The reader distinguishes nulls, booleans, currency, date serials and binary values. Unsupported schemas, hidden/system-maintained user columns, encrypted files, complex fields and overflow structures refuse rather than return an incomplete ordinary-table result. System catalogs are excluded: this is table-subset reading, not whole-database validation. Access writes remain blocked.

Independent review repaired column-identity and hidden-column checks. Integration removed the obsolete unsupported-container guard for these two read formats and retained write protection. Source147 retains all Source146 features.

Status: reviewed source only. Installation, runtime integration and Telegram acceptance are pending; the operational version remains Source117.
