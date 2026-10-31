# V01 presentation reader: accepted source, not installed

This block preserves the accepted cumulative native patch for bounded offline
PPTX/ODP reading. It adds native slide text, tables, cached chart values, diagram
text and separate speaker notes to the ordinary document descriptor path. Slide
order, hidden content, source labels and unsupported features remain explicit.
The existing descriptor and mid-read revocation boundaries are retained.

The patch changes `tools/read_extract.py`, `hermes_cli/friday_user_scope.py` and
`hermes_cli/friday_prompt_scope.py`, and adds `tools/scoped_presentation.py`.
`manifest.json` records exact preimage and accepted source hashes. Applying the
patch in memory to those preimages reproduced all four accepted files exactly.
It is an analysis artifact; publication does not apply it to an installed product.

Four reviewed reader faults are corrected:

- An ODF range ending in another table remains unresolved instead of reporting
  values from the local table.
- ZIP member names truncated at NUL are rejected using their original identity.
- PPTX slide, notes, chart and diagram parts must match their declared content
  types and supported XML roots.
- Chart series and caches must occupy supported connected locations; numeric
  fields reject string sources, and diagram points reject disconnected structure,
  duplicate identities and ambiguous text.

Run the portable, standard-library controls from this directory:

```sh
python3 -B controls.py
```

The controls verify both the patch and parser hashes, load the exact new parser
from the patch in memory, and generate neutral synthetic archives in memory.
They cover positive PPTX/ODP extraction and the corrected failure cases.
All 17 controls passed; `controls-result.json` records this bounded result.
Four targeted checks also reproduced their corresponding faults on the retained
pre-fix parser, confirming that the portable checks detect the reviewed defects.
They do not exercise application installation, live authority or the whole reader
dispatch. Existing source acceptance retained 46 author controls, 23 independent
reviewer controls and 13 independent changed-delta controls; those unchanged
results were reused rather than rerun for publication.

A genuine PPTX was observed during the retained source review with five slides,
five separate note parts, a native table and cached chart data. No genuine file
or its content is published here. ODP and diagram examples remain synthetic only.

This is a native XML and cached-data view. Embedded workbooks and formulas are
not evaluated or refreshed. Rendering, images/OCR, master/layout/style inheritance
and diagram layout are outside its coverage. No Office, model or messaging
execution was performed for this publication block.

Installed Source114 remains unchanged. Installation, runtime and semantic user
acceptance have not occurred for this reader. Integration with the separate
write/export work and the supported source inventory remains pending. The full
presentation family of 15 formats, 161 native rows and 10 conversions is
unaccepted; the overall 170/120/all-variants gates are also unaccepted. These
controls provide no full-family or product-readiness claim.
