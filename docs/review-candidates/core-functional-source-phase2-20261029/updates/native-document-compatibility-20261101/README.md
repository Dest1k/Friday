# Native document compatibility, 2026-11-01

Accepted source components; uninstalled. Installed product remains Source117. This patch supplements the earlier binary-template and Source136 materials; it is not an installation or live acceptance record.

- DOC/DOT reads stored main-story text and cached HYPERLINK results, with exact field-position checks. Instructions and targets are not followed or evaluated. A genuine Microsoft Word template now matches independently extracted text, including three cached link labels. Empty command tables and explicitly bounded passive metadata are handled; macros, other active fields and frames remain refused.
- ODB accepts the registered `.base` MIME type and its deprecated `.database` alias while requiring exact package/manifest agreement. Four unchanged LibreOffice originals pass. Results contain declared metadata, not database rows or executed queries.
- PDF preserves the trusted glyph proof while accepting the retained Liberation bullet's proven horizontal-only hint behavior and safe white polygon fills. The complete retained PDF remains refused at a separate colored-paint boundary.

Independent reviews passed: DOC/DOT 1907 checks; PDF font delta 51 checks and white-polygon delta 54 checks. Root independently checked the ODB delta and all four genuine files. Local regressions and negative controls accompany each component privately.

Documentation clarifications: Word's limit is 400000 total CP; URL-shaped stored display labels are retained. These labels differ from the omitted field instructions and link destinations. Stored text does not establish rendering, formatting or hidden/revision visibility.

Primary format references: [IANA ODB registration](https://www.iana.org/assignments/media-types/application/vnd.oasis.opendocument.base), [MS-DOC field PLC](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-doc/751b09bb-72f0-45ef-8e87-666dea68219f).
