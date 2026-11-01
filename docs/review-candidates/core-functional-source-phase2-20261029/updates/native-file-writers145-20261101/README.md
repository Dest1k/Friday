# Source145 native file operations

Source-only integration of four bounded native creation and new-copy editing routes: XPS/OpenXPS, Visio XML (VDX), binary Excel (XLSB), and EPUB3. Existing source files remain unchanged; edits use the current source hash and create a new destination through the ordinary scoped file operation.

XPS/OpenXPS covers explicit fixed-page text with an embedded font and editing of the recognized text-only profile. VDX covers explicit shapes/connections and selected plain shape text. XLSB covers explicitly typed scalar cells and same-type selected-cell edits. EPUB3 covers explicit book metadata/chapters and selected plain XHTML paragraphs, preserving other member payloads and checked ZIP metadata.

Unsupported structures refuse with explicit limits. These results do not establish Office/Visio/EPUB renderer compatibility, visual fidelity, or support for every possible input. Local implementation and integration checks are separate from installation and user acceptance. The installed operational source remains117; live/Telegram checks are deferred.

This publication includes the independently reviewed source delta and a compact record of local observations. Original failed controls and corrections remain distinguished from the accepted result.

Validation:365 local controls passed on the initial coherent merge;103 independent integration controls passed, with the final prompt correction checked by Root in12 targeted cases. These counts describe separate verification passes, not unique end-user scenarios.
