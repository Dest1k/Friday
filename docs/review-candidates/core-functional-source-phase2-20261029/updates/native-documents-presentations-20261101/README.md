Native document and presentation source package

This patch extends the accepted Source120 native source with ODT document operations, native presentation profiles and exact text revision, and selected-slide merging for ODP/OTP/FODP. It includes the preceding ODT source component, so apply this aggregate patch directly to Source120 rather than after that individual patch.

Independent reviews and local consumer checks include the real atomic publication functions with disposable files. The final combined snapshot passed 84 presentation/text/serialization checks and 39 ODT checks. The manifest records exact before/after bytes for all 14 files.

This is reviewed source, not an installed or live-accepted release. Office, Telegram and visual checks remain pending. Unsupported content, incompatible styles, ambiguous edits, changed inputs and reused destinations are refused. Existing files are preserved.
