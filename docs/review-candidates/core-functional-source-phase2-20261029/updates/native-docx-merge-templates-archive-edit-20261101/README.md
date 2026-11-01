Native DOCX merge, legacy template reading and archive member edits

DOCX merge now combines exactly two supported own-workspace packages into a new DOCX. It retains body paragraphs, tables and inline PNG/JPEG, remapping image and drawing identifiers. Global style/settings/metadata parts must match, and final section properties must be compatible. Unsupported fields, numbering, links and structures refuse. The input files remain unchanged.

DOT and XLT gain explicit inert read profiles with genuine native template markers. They remain read-only. Independent structural fixtures cover positive parsing and rejection controls; a supported real producer positive is still pending. Unsupported available real template inputs were refused and are not counted as positive acceptance.

The archive_edit operation creates a new ZIP or TAR-family archive with explicitly requested replacements, append operations and exact member removals. Retained names, order and payload bytes remain intact; container metadata is normalized. Removing a directory entry does not implicitly remove its descendants. Source snapshots and replacements retain the existing publication, cancellation and uncertain-effect protections. 7z editing is unsupported.

This nine-file patch follows the raster/MHTML source block a246d2645e3bd3858e380cd2d37715777a926d23. The final combined native source passed 91 local controls and 16 independent integration controls, with unchanged component reviews reused. These are source results: installed Source117 remains unchanged, and Office, Telegram and live acceptance are pending.
