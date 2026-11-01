# VDX and bounded compressed RAR4 readers

Source-only preparation against the accepted Source136 native snapshot. Installed Source117 and live services are unchanged; this is not runtime or full-product acceptance. The separate PPT/POT/PPS integration is still pending.

Standalone VDX now exposes stored page labels, shape/group IDs and declared Connects. Master/style/background/geometry/formula evaluation and flow inference remain unsupported. Action definitions are not executed or returned. Formula-dependent line ends remain UNKNOWN, and a generic extracted read cannot authorize raw text overwrite of a VDX file. Two unchanged publisher VDX examples were read; their stored action definitions remain inert.

RAR4 adds a restricted version29 LZ/Huffman decoder that requires the actual compressed end marker and validates the complete decoded bytes against the isolated native decoder. Header size and CRC alone cannot authorize a truncated prefix. Stored RAR4 and supported RAR5 remain available. PPMd, VM filters, older compression versions, solid/encrypted/multivolume archives and unsafe members remain unsupported. Original archive refusals and earlier observations are preserved.

The combined eight-file source delta passed 53 focused local tests after independent reviews. The VDX review found and fixed three issues before acceptance: formula disclosure, generic overwrite protection and contradictory guidance. RAR4 review covered entropy termination, Huffman tables, history and distance boundaries, forged sizes, output limits, cancellation and worker cleanup. Check counts describe individual runs and are not a distinct-case total.

The patch includes the BSD-2-Clause attribution for the RAR algorithm reference. VDX sample provenance: [VisioAutomation.VDX](https://github.com/saveenr/VisioAutomation.VDX/tree/61368311a43b0d3cec6d5296b7e20b390d5d2e85), MIT. No original sample documents or private working evidence are included here.
