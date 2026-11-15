# GPGME helper stop and trace serialization — SOURCE only

Exact reviewed R1 plus save-only R2: four final Python source files and both original
patches. This is a conditional source archive, with external dependencies. It is
not installed or enabled. Runtime, helper liveness, actual M and user acceptance
are unqualified.

R1 selects an explicitly stopped original thread/frame, preserves the first
refusal, defers stop/exit dispatch and restores the original context after a
guarded selected-child drain. The GNU17.1 safety argument depends on ordinary
successful all-stop command entry, no-`&` commands and exclusive fixed callbacks.
It does not prove child progress: the global inline step-over state may defer
execution. Actual exits, absence and restoration require separate qualification.

R2 changes only `save()`: emitted JSON excludes exactly `helper_event_depth` and
`gpgme_drain_active`; internal STATE, extensions, first error and diagnostics remain.
Strict checker and G2 schemas are unchanged. Earlier serialization controls use
invented inputs and establish source/schema behavior only.

[Dependencies and patch sequence](SOURCE-DEPENDENCIES.json) name the four exact
public predecessors. Apply original `HELPER-STOP.patch` by that explicit role
mapping, then `SERIALIZATION-R2.patch` to the R1 observer. The absolute patch
headers are preserved as provenance, not live destination paths. Context bytes,
including single-space blank context lines, are unchanged. The sequence recreates
all four archived final files exactly.

The pending-fork and post-starti archives remain immutable predecessors. The
ordinary native factory is independent work; completing it is not a prerequisite
for OwnC source review or separately admitted finite OwnC qualification. This
archive does not claim that factory or the full runtime graph is complete.

[Source status and private evidence pins](SOURCE-STATUS.json),
[GNU primary-source metadata](PRIMARY-SOURCE-METADATA.json) and the
[exact public manifest](PUBLIC-MANIFEST.json) preserve provenance and limits.
Earlier reviews and source controls are reused by hash, not presented as new runs.
The archive task checked copies, patch reconstruction, AST compilation, references
and the publication allowlist; it did not import or execute the product.

OwnC5bb/7d8 are CLOSED. Their effects, ONCE and clocks are not replayed. The old
generic GDB message/callsite was not captured; these static fixes do not establish
its historical cause or actual kernel execution. No runtime plans, grants, logs,
private fixtures, user data, credentials, binaries or GNU upstream source are
included. Original executable bytes and patch path literals are retained. Root
alone owns integration and any separately admitted current runtime qualification.
