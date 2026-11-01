Native raster and MHTML operations

Raster input now exposes every bounded frame with geometry and pixel identity, including multi-page TIFF. The explicit image_transform operation selects one numbered frame, crops in orientation-normalized coordinates, rotates clockwise and writes a new supported image. All source frames are checked first. Only losslessly representable RGBA8 input modes are supported; high-depth, floating-point and non-RGB modes refuse. JPEG output is explicitly lossy. Metadata is omitted after applying EXIF orientation. This operation does not perform OCR or visual interpretation.

MHTML/MHT gains native root-HTML text/table reading, genuine multipart/related creation from literal text or structured blocks, and a unique literal text-run edit in a new copy. Edits preserve the envelope, headers and non-target MIME parts. Scripts, ambiguous MIME, raw-text/conditional HTML models and unsupported structures refuse; external resources are never fetched. CSS, images and layout are not rendered.

Both components passed local scoped operations, independent source/negative controls and parent checks of reviewer fixes. Raster corrections cover reply size, TIFF orientation metadata and hidden precision loss. MHTML corrections cover raw-text edit semantics and text outside the root structure. The eight-file patch was replayed against all recorded before/after hashes.

Reviewed source only, after native archive commit a2cd982fbd96f51b8a2bd6c0fbe3329a2c002b70. Installed Source117 is unchanged; deployment and live user acceptance remain pending.
