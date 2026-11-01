# Bounded HEIF pixel reading and conversion — Source148

Adds native reading of a direct 8-bit HEVC HEIC/HEIF profile through isolated workers using existing pinned system codec libraries. Reads register all top-level images with native YUV plane hashes and color metadata. Selected images can be converted to a new raster file, with crop and clockwise rotation.

Conversion requires an explicit BT.601 or BT.709 matrix and refuses disagreement with declared metadata. Unknown primaries and transfer characteristics remain unknown. Pixel aspect ratio is reported; transformations use stored samples without aspect resampling. This does not establish display equivalence, visual interpretation, OCR or color fidelity.

The decoder admits only the reviewed codec ABI and runs inside a confined process with bounded input/output, time, memory and CPU. Unsupported transforms, ICC profiles, derived/auxiliary items, external references, depth and malformed data refuse. Source files remain unchanged; HEIF output creation is unsupported.

Status: independently reviewed source, including real HEIF input, pixel conversion, containment, cancellation and existing raster regressions. Installation, service runtime and Telegram acceptance remain pending. Operational Source117 is unchanged.
