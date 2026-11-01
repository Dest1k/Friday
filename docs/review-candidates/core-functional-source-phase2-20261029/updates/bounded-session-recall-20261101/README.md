Bounded session recall and rewound-preview visibility

This source-only change limits serialized history responses and adds recoverable pages for tool-call JSON. Native reads decode only the selected head/tail rows; message identifiers and continuation offsets remain available. Rewound rows no longer supply browse previews; archived compacted originals remain visible.

Root local checks:17; independent review:41. The same three leaves were composed with the reviewed Dashboard change and passed26 local checks. The reviewer fixed pagination progress, false continuation metadata, malformed Unicode handling and the adjacent preview query; Root checked that delta.

Selected very large fields still materialize before shaping. Oversized structured content/metadata may be refused. Existing hidden-source and cross-user policies are preserved. Future carrier, installation and user-level acceptance remain pending; installed Source117 is unchanged.
