# Calc GPGME cached postload lifecycle R3 — SOURCE only

This archive contains the three exact reviewed source afterimages and the original
baseline-to-R3 patch. The adapter bounds readiness reentry; collector and OwnC
driver bind the completed-load cached getter to exact caller, LWP and marker
proofs, full query/restore/close predicates and the held1 → held2 transition.
Initial LOAD_OPEN spawning and closure stay unchanged. A separate source addendum
checks refusal of a late LOAD_OPEN fork event after finish/guard retirement.

[Source status and limits](SOURCE-STATUS.json), [role/header mappings and exact
beforeimages](SOURCE-DEPENDENCIES.json), [provenance](PROVENANCE.json) and the
[public file manifest](PUBLIC-MANIFEST.json) describe this bounded publication.
The exact afterimages are [adapter](source/gpgme_engine_gdb.py),
[collector](source/gpgme_boundary_collector.py) and
[OwnC driver](source/ownc_gdb.py).

Reconstruct in an isolated work directory: copy each named public beforeimage to
its mapped role path, then apply the [original patch](CACHED-POSTLOAD-LIFECYCLE.patch)
with `patch --fuzz=0 --batch --forward -p1`. Require zero offsets and the three
exact final SHA-256 values. Preserve blank context bytes. The committed sibling
beforeimages reconstruct all three sources without private inputs. External
runtime dependencies remain unbundled; this is not a standalone execution capsule.

V1 was blocked by missing late checks and bindings; R2 was blocked by readiness
reentry. Both remain unadmitted history. The final R3 functional source review is
reused unchanged. Its synthetic GDB/OS/initial-child/paper-custody/held-host/native
leaves do not prove runtime or semantic acceptance. The own-fixture SHA allowlist
identifies test code; it does not accept user documents.

Ordinary/fullV3, METRIC and other gpgmepp caller support remain unproved. Named
libmergedlo.so is 109787088 bytes, above the unchanged 33554432-byte caller bound.
OwnC source proof does not establish the ordinary user path. Root independently
owns any separate runtime admission and qualification; future actual results are
unknown at this source snapshot. Actual M and semantic/fullV3 acceptance are not
claimed. Old clocks, consumed/UNKNOWN effects and cleanup obligations stay intact.

Private references and hashes provide provenance only, not execution authority or
public reproduction of private tests. No upstream source copies, binaries/cache,
vendor trees, private full manifests/plans/grants/runtime, user documents or
credentials are published.
