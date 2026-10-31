# Literal table repair: accepted source, not installed

The original response returned two artifacts when one was requested. Its CSV
passed an exact-string static check, but ordinary Office open, resave and reopen
introduced native formulas and coerced textual identifiers into numbers. The TSV
also had malformed multiline boundaries; ordinary default import was not
qualified. The original S16 case remains **FAIL**, with its partial **UNKNOWN**
observation and **full180=false** preserved. Closed effects were not replayed.

This block preserves three exact accepted source leaves and their original
relative-path patch. It adds bounded, inert JSON records for stored XLSX cells to
the ordinary reader, guides one requested literal-text table toward one XLSX,
and serializes literal carriage returns as XML character references in both
existing XLSX writer paths. The output-count rule is guidance; actual model
compliance or returned artifact count has not been established.

The records preserve XML-parsed inline/shared base text, native lexical values,
cell coordinates, declared rows, preview positions, native types and style
indices. Native formulas and their missing, empty or present saved caches are
separate from literal values and are never evaluated. TAB, LF, CR and Unicode
are JSON escaped. Only stored cells are recorded: sparse gaps and merged
followers are not invented. The old TAB/LF display remains available with an
explicit warning that it is not a lossless table stream.

Run the portable standard-library controls from this directory:

```sh
python3 -B controls.py
```

All 12 controls passed; `controls-result.json` contains the bounded result.
They verify the exact three source hashes, reverse the patch in memory to
reconstruct all declared preimages, and reapply it to reproduce the accepted
bytes. They execute the actual published extractor on neutral synthetic OOXML
archives generated in memory. Both LF-versus-real-rows and TAB-versus-real-cells
collisions are reproduced on the exact preimage extractor; the new records
distinguish them. Controls also cover escaped literals, formula/cache separation,
shared strings, unresolved indices, sparse/merged/hidden scope and explicit
record, text, byte, row and column omissions.

These portable checks do not exercise the writer, full nearest consumers,
authority, native `read_file` pagination, installation, runtime, Office, model
generation, messaging or user acceptance. Retained source acceptance reused 12
author tests (one invokes four selected legacy checks), independent delta review
and six integrator checks. Those counts are not added together as independent
tests. The retained writer/XML and actual nearest-consumer evidence is referenced
only by safe source/result digests in `manifest.json`; its private inputs and
dependencies are not copied or rerun for publication.

The projection is bounded to visible-sheet preview cells: at most 5,000 row
elements per sheet, 256 columns, 1,024 records, 4,096 characters per bounded text
field, 32,768 bytes per record and 256,000 bytes for the typed preview, inside the
existing 1,000,000-byte extracted-text cap. Existing formula and structure
sections retain budget priority, so the typed projection may be omitted. Hidden
sheets stay outside this cell scope; hidden rows/columns are not filtered.
Inspect independent row/column omissions and sheet scope even when the record
`truncated` flag is false. Check `cell_records.location` before parsing a section:
source text in the old display can imitate its heading. Native `read_file` can
split a JSON line, requiring same-line `char_offset` fragments to be joined first.

OOXML `ST_Xstring` logical `_xHHHH_` decoding/encoding remains explicit technical
debt. XML-level CR/CRLF preservation does not establish Office-decoded equality
or reopen/resave/reopen acceptance. Formatting, date/style interpretation, rich
formatting, charts, comments, layout, formula evaluation and full-workbook
coverage are outside this result. No whole format family or product PASS follows.

This is **SOURCE_ACCEPTED_NOT_INSTALLED**. The snapshots are candidates against
their declared preimages, not a merged installed release. Separate presentation
work still needs its common merge and final dialogue revision; Source115 is not
bound. Installed Source114 and services are unchanged. Actual model behavior,
one-artifact delivery, ordinary Office and semantic user acceptance remain
unestablished. The full 170/120/all-variants gates remain unaccepted.

`manifest.json` records exact relative preimage/after hashes. `SHA256SUMS` covers
every published file except itself. The standard OOXML namespace URIs in source
and synthetic XML are format identifiers, not deployment endpoints. No genuine
user file, user-file hash, credential, private handoff, local deployment path,
raw log or remote deployment address is included.
